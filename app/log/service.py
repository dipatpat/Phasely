import datetime
import json
import uuid
from decimal import Decimal

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.client.service import get_client_profile_by_profile_id
from app.core.enums import CyclePhase, MealType
from app.exercise.schemas import ExercisePublic
from app.exercise.service import ExerciseNotFound, get_exercise_by_id
from app.log.models import DailyLog, ExerciseLog, MealLog
from app.recipe.models import Recipe, RecipeIngredient
from app.recipe.schemas import RecipePublic
from app.recipe.service import RecipeNotFoundError, get_recipe_by_id
from app.recommendation.service import (
    calculate_cycle_length,
    calculate_cycle_phase,
    create_period_log,
    get_exercise_recommendations,
    get_period_start_dates,
    get_recipe_recommendations,
)


class DailyLogAlreadyExistsError(Exception):
    pass


class InsufficientCycleDataError(Exception):
    pass


async def create_daily_log(
    db: AsyncSession,
    client_id: uuid.UUID,
    log_date: datetime.date,
    period_started_today: bool,
    cycle_phase: CyclePhase | None,
    hours_of_sleep: Decimal | None,
    energy_level: int | None,
    redis: aioredis.Redis,
) -> tuple[DailyLog, list[RecipePublic], list[ExercisePublic]]:
    if period_started_today:
        await create_period_log(db, client_id, log_date)

    if cycle_phase is None:
        period_starts = await get_period_start_dates(db, client_id)
        if period_starts:
            last_period_start = max(period_starts)
            cycle_length_days = calculate_cycle_length(period_starts)
        else:
            last_period_start = None
            cycle_length_days = None

        client_profile = await get_client_profile_by_profile_id(db, client_id)

        if last_period_start is None:
            last_period_start = client_profile.last_period_start
        if cycle_length_days is None:
            cycle_length_days = client_profile.cycle_length_days

        if last_period_start is None or cycle_length_days is None:
            raise InsufficientCycleDataError(
                "Not enough data to calculate cycle phase; please provide it manually"
            )

        cycle_phase = calculate_cycle_phase(
            last_period_start,
            cycle_length_days,
            client_profile.period_length_days,
            log_date,
        )

    new_log = DailyLog(
        client_id=client_id,
        log_date=log_date,
        cycle_phase=cycle_phase,
        hours_of_sleep=hours_of_sleep,
        energy_level=energy_level,
    )
    try:
        db.add(new_log)
        await db.commit()
        await db.refresh(new_log)
    except IntegrityError as e:
        await db.rollback()
        raise DailyLogAlreadyExistsError("Daily log already exists") from e
    recipes, exercises = await trigger_recommendation(
        db, redis, client_id, log_date, cycle_phase, energy_level
    )
    return new_log, recipes, exercises


async def trigger_recommendation(
    db: AsyncSession,
    redis: aioredis.Redis,
    client_id: uuid.UUID,
    log_date: datetime.date,
    cycle_phase: CyclePhase,
    energy_level: int | None,
) -> tuple[list[RecipePublic], list[ExercisePublic]]:
    cache_key = f"recommendations:{client_id}:{log_date}"
    cached_data = await redis.get(cache_key)
    if cached_data:
        cached_data = json.loads(cached_data)
        recipes = [
            RecipePublic.model_validate(recipe) for recipe in cached_data["recipes"]
        ]
        exercises = [
            ExercisePublic.model_validate(exercise)
            for exercise in cached_data["exercises"]
        ]
        return recipes, exercises
    day_of_week = log_date.isoweekday()
    recipes_from_db = await get_recipe_recommendations(db, client_id, cycle_phase)
    exercises_from_db = await get_exercise_recommendations(
        db, client_id, cycle_phase, day_of_week, energy_level
    )
    recipes = [RecipePublic.model_validate(recipe) for recipe in recipes_from_db]
    exercises = [
        ExercisePublic.model_validate(exercise) for exercise in exercises_from_db
    ]
    cache_payload = json.dumps(
        {
            "recipes": [recipe.model_dump(mode="json") for recipe in recipes],
            "exercises": [exercise.model_dump(mode="json") for exercise in exercises],
        }
    )
    await redis.set(cache_key, cache_payload, ex=86400)
    return recipes, exercises


async def get_daily_log_by_id(db: AsyncSession, log_id: uuid.UUID) -> DailyLog | None:
    result = await db.execute(select(DailyLog).where(DailyLog.id == log_id))
    return result.scalar_one_or_none()


async def get_daily_log_by_client_and_date(
    db: AsyncSession, client_id: uuid.UUID, log_date: datetime.date
) -> DailyLog | None:
    result = await db.execute(
        select(DailyLog).where(
            DailyLog.client_id == client_id, DailyLog.log_date == log_date
        )
    )
    return result.scalar_one_or_none()


async def create_meal_log(
    db: AsyncSession,
    client_id: uuid.UUID,
    recipe_id: uuid.UUID,
    meal_type: MealType,
    consumed_at: datetime.datetime,
    portion_quantity: Decimal,
    portion_unit: str,
) -> MealLog:
    recipe = await get_recipe_by_id(db, recipe_id)
    if recipe is None:
        raise RecipeNotFoundError("Recipe not found")
    new_log = MealLog(
        client_id=client_id,
        recipe_id=recipe_id,
        meal_type=meal_type,
        consumed_at=consumed_at,
        portion_quantity=portion_quantity,
        portion_unit=portion_unit,
    )
    db.add(new_log)
    await db.commit()
    return await get_meal_log_by_id(db, new_log.id)


async def get_meal_log_by_id(db: AsyncSession, log_id: uuid.UUID) -> MealLog | None:
    result = await db.execute(
        select(MealLog)
        .options(
            selectinload(MealLog.recipe)
            .selectinload(Recipe.ingredients)
            .selectinload(RecipeIngredient.ingredient),
            selectinload(MealLog.recipe).selectinload(Recipe.dietary_tags),
        )
        .where(MealLog.id == log_id)
    )
    return result.scalar_one_or_none()


async def get_exercise_log_by_id(
    db: AsyncSession, log_id: uuid.UUID
) -> ExerciseLog | None:
    result = await db.execute(
        select(ExerciseLog)
        .options(selectinload(ExerciseLog.exercise))
        .where(ExerciseLog.id == log_id)
    )
    return result.scalar_one_or_none()


async def create_exercise_log(
    db: AsyncSession,
    client_id: uuid.UUID,
    exercise_id: uuid.UUID,
    completed_at: datetime.datetime,
    notes: str | None = None,
) -> ExerciseLog:
    exercise = await get_exercise_by_id(db, exercise_id)
    if exercise is None:
        raise ExerciseNotFound("Exercise not found")

    new_log = ExerciseLog(
        client_id=client_id,
        exercise_id=exercise_id,
        completed_at=completed_at,
        notes=notes,
    )
    db.add(new_log)
    await db.commit()

    return await get_exercise_log_by_id(db, new_log.id)
