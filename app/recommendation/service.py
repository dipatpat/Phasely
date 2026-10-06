import uuid
from datetime import date

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CyclePhase
from app.exercise.models import Exercise
from app.log.models import PeriodLog
from app.plan.service import (
    get_active_nutrition_plan_by_client_id,
    get_active_training_plan_by_client_id,
)
from app.recipe.models import Recipe

LUTEAL_LENGTH_DAYS = 14
OVULATION_WINDOW_DAYS = 3
ENERGY_INTENSITY_RULES = [
    {"min_energy": 0, "max_energy": 3, "allowed_difficulty": ["easy"]},
    {"min_energy": 4, "max_energy": 7, "allowed_difficulty": ["easy", "medium"]},
    {
        "min_energy": 8,
        "max_energy": 10,
        "allowed_difficulty": ["easy", "medium", "hard"],
    },
]


def calculate_cycle_phase(
    last_period_start: date,
    cycle_length_days: int,
    period_length_days: int,
    target_date: date,
) -> CyclePhase:
    day_of_cycle = ((target_date - last_period_start).days % cycle_length_days) + 1
    luteal_start_day = cycle_length_days - LUTEAL_LENGTH_DAYS + 1
    ovulatory_start_day = luteal_start_day - OVULATION_WINDOW_DAYS

    if day_of_cycle <= period_length_days:
        return CyclePhase.menstrual
    elif day_of_cycle < ovulatory_start_day:
        return CyclePhase.follicular
    elif day_of_cycle < luteal_start_day:
        return CyclePhase.ovulatory
    else:
        return CyclePhase.luteal


def calculate_cycle_length(period_starts: list[date]) -> int | None:
    if len(period_starts) < 2:
        return None
    sorted_starts = sorted(period_starts)
    return (sorted_starts[-1] - sorted_starts[-2]).days


async def create_period_log(
    db: AsyncSession, client_id: uuid.UUID, period_start_date: date
) -> PeriodLog:
    new_entry = PeriodLog(client_id=client_id, period_start_date=period_start_date)
    db.add(new_entry)
    await db.commit()
    await db.refresh(new_entry)
    return new_entry


async def get_period_start_dates(db: AsyncSession, client_id: uuid.UUID) -> list[date]:
    result = await db.execute(
        select(PeriodLog.period_start_date).where(PeriodLog.client_id == client_id)
    )
    return list(result.scalars().all())


async def get_recipe_recommendations(
    db: AsyncSession, client_id: uuid.UUID, cycle_phase: CyclePhase
) -> list[Recipe]:
    plan = await get_active_nutrition_plan_by_client_id(db, client_id)
    if plan is None:
        return []
    return [
        assignment.recipe
        for assignment in plan.recipes
        if assignment.cycle_phase == cycle_phase
    ]


def get_allowed_difficulty_levels(energy_level: int | None) -> list[str] | None:
    if energy_level is None:
        return None
    for rule in ENERGY_INTENSITY_RULES:
        if rule["min_energy"] <= energy_level and energy_level <= rule["max_energy"]:
            return rule["allowed_difficulty"]
    return None


async def get_exercise_recommendations(
    db: AsyncSession,
    client_id: uuid.UUID,
    cycle_phase: CyclePhase,
    day_of_week: int,
    energy_level: int | None,
) -> list[Exercise]:
    plan = await get_active_training_plan_by_client_id(db, client_id)
    if plan is None:
        return []
    allowed_exercises = [
        allowed_exercise
        for allowed_exercise in plan.exercises
        if allowed_exercise.cycle_phase == cycle_phase
        and allowed_exercise.day_of_week == day_of_week
    ]
    allowed_difficulty = get_allowed_difficulty_levels(energy_level)
    if allowed_difficulty is not None:
        allowed_exercises = [
            exercise
            for exercise in allowed_exercises
            if exercise.difficulty_level in allowed_difficulty
        ]
    return [assignment.exercise for assignment in allowed_exercises]


async def invalidate_recommendations_cache(
    redis: aioredis.Redis, client_id: uuid.UUID
) -> None:
    cache_key = f"recommendations:{client_id}:{date.today()}"
    await redis.delete(cache_key)
