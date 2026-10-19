import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.client.service import get_client_profile_by_profile_id
from app.core.enums import CyclePhase, DifficultyLevel
from app.exercise.models import Exercise
from app.log.models import PeriodLog
from app.plan.models import (
    NutritionPlan,
    NutritionPlanRecipe,
    TrainingPlan,
    TrainingPlanExercise,
)
from app.recipe.models import Recipe, RecipeIngredient

LUTEAL_LENGTH_DAYS = 14
OVULATION_WINDOW_DAYS = 3
CYCLE_PHASE_RULES = [
    {"phase": CyclePhase.menstrual, "ends_at": "period_end", "offset_days": 0},
    {
        "phase": CyclePhase.follicular,
        "ends_at": "cycle_end",
        "offset_days": -(LUTEAL_LENGTH_DAYS + OVULATION_WINDOW_DAYS),
    },
    {
        "phase": CyclePhase.ovulatory,
        "ends_at": "cycle_end",
        "offset_days": -LUTEAL_LENGTH_DAYS,
    },
    {"phase": CyclePhase.luteal, "ends_at": "cycle_end", "offset_days": 0},
]
ENERGY_INTENSITY_RULES = [
    {
        "min_energy": 0,
        "max_energy": 3,
        "allowed_difficulty": [DifficultyLevel.easy],
    },
    {
        "min_energy": 4,
        "max_energy": 7,
        "allowed_difficulty": [DifficultyLevel.easy, DifficultyLevel.medium],
    },
    {
        "min_energy": 8,
        "max_energy": 10,
        "allowed_difficulty": [
            DifficultyLevel.easy,
            DifficultyLevel.medium,
            DifficultyLevel.hard,
        ],
    },
]


def calculate_cycle_phase(
    last_period_start: date,
    cycle_length_days: int,
    period_length_days: int,
    target_date: date,
) -> CyclePhase:
    day_of_cycle = ((target_date - last_period_start).days % cycle_length_days) + 1
    anchors = {"period_end": period_length_days, "cycle_end": cycle_length_days}
    for rule in CYCLE_PHASE_RULES:
        if day_of_cycle <= anchors[rule["ends_at"]] + rule["offset_days"]:
            return rule["phase"]
    return CYCLE_PHASE_RULES[-1]["phase"]


def calculate_cycle_length(period_starts: list[date]) -> int | None:
    if len(period_starts) < 2:
        return None
    sorted_starts = sorted(period_starts)
    return (sorted_starts[-1] - sorted_starts[-2]).days


@dataclass(frozen=True)
class CycleParameters:
    last_period_start: date
    cycle_length_days: int
    period_length_days: int

    def phase_on(self, target_date: date) -> CyclePhase:
        return calculate_cycle_phase(
            self.last_period_start,
            self.cycle_length_days,
            self.period_length_days,
            target_date,
        )


async def get_cycle_parameters(
    db: AsyncSession, client_id: uuid.UUID
) -> CycleParameters | None:
    period_starts = await get_period_start_dates(db, client_id)
    last_period_start = max(period_starts) if period_starts else None
    cycle_length_days = calculate_cycle_length(period_starts)

    client_profile = await get_client_profile_by_profile_id(db, client_id)
    if last_period_start is None:
        last_period_start = client_profile.last_period_start
    if cycle_length_days is None:
        cycle_length_days = client_profile.cycle_length_days

    if last_period_start is None or cycle_length_days is None:
        return None
    return CycleParameters(
        last_period_start=last_period_start,
        cycle_length_days=cycle_length_days,
        period_length_days=client_profile.period_length_days,
    )


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
    result = await db.execute(
        select(Recipe)
        .join(NutritionPlanRecipe, NutritionPlanRecipe.recipe_id == Recipe.id)
        .join(NutritionPlan, NutritionPlanRecipe.nutrition_plan_id == NutritionPlan.id)
        .where(
            NutritionPlan.client_id == client_id,
            NutritionPlan.is_active.is_(True),
            NutritionPlanRecipe.cycle_phase == cycle_phase,
        )
        .options(
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient),
            selectinload(Recipe.dietary_tags),
        )
    )
    return list(result.scalars().all())


def get_allowed_difficulty_levels(
    energy_level: int | None,
) -> list[DifficultyLevel] | None:
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
    query = (
        select(Exercise)
        .join(TrainingPlanExercise, TrainingPlanExercise.exercise_id == Exercise.id)
        .join(TrainingPlan, TrainingPlanExercise.training_plan_id == TrainingPlan.id)
        .where(
            TrainingPlan.client_id == client_id,
            TrainingPlan.is_active.is_(True),
            TrainingPlanExercise.cycle_phase == cycle_phase,
            TrainingPlanExercise.day_of_week == day_of_week,
        )
    )
    allowed_difficulty = get_allowed_difficulty_levels(energy_level)
    if allowed_difficulty is not None:
        query = query.where(
            TrainingPlanExercise.difficulty_level.in_(allowed_difficulty)
        )
    result = await db.execute(query)
    return list(result.scalars().all())
