import datetime
import json
import uuid
from decimal import Decimal

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import APP_TZ
from app.core.enums import CyclePhase, MealType
from app.exercise.service import ExerciseNotFound, get_exercise_by_id
from app.log.models import DailyLog, ExerciseLog, MealLog
from app.plan.schemas import TrainingPlanExercisePublic
from app.recipe.models import Recipe, RecipeIngredient
from app.recipe.schemas import RecipePublic
from app.recipe.service import RecipeNotFoundError, get_recipe_by_id
from app.recommendation.service import (
    create_period_log,
    get_cycle_parameters,
    get_exercise_recommendations,
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
) -> tuple[DailyLog, list[RecipePublic], list[TrainingPlanExercisePublic]]:
    if period_started_today:
        await create_period_log(db, client_id, log_date)

    if cycle_phase is None:
        cycle_parameters = await get_cycle_parameters(db, client_id)
        if cycle_parameters is None:
            raise InsufficientCycleDataError(
                "Not enough data to calculate cycle phase; please provide it manually"
            )
        cycle_phase = cycle_parameters.phase_on(log_date)

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
) -> tuple[list[RecipePublic], list[TrainingPlanExercisePublic]]:
    cache_key = f"recommendations:{client_id}:{log_date}"
    cached_data = await redis.get(cache_key)
    if cached_data:
        cached_data = json.loads(cached_data)
        recipes = [
            RecipePublic.model_validate(recipe) for recipe in cached_data["recipes"]
        ]
        exercises = [
            TrainingPlanExercisePublic.model_validate(exercise)
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
        TrainingPlanExercisePublic.model_validate(exercise)
        for exercise in exercises_from_db
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


def _day_bounds(
    start_date: datetime.date, end_date: datetime.date
) -> tuple[datetime.datetime, datetime.datetime]:
    start = datetime.datetime.combine(start_date, datetime.time.min, tzinfo=APP_TZ)
    end = datetime.datetime.combine(
        end_date + datetime.timedelta(days=1), datetime.time.min, tzinfo=APP_TZ
    )
    return start, end


async def list_daily_logs(
    db: AsyncSession,
    client_id: uuid.UUID,
    start_date: datetime.date,
    end_date: datetime.date,
) -> list[DailyLog]:
    result = await db.execute(
        select(DailyLog)
        .where(
            DailyLog.client_id == client_id,
            DailyLog.log_date.between(start_date, end_date),
        )
        .order_by(DailyLog.log_date)
    )
    return list(result.scalars().all())


async def list_meal_logs(
    db: AsyncSession,
    client_id: uuid.UUID,
    start_date: datetime.date,
    end_date: datetime.date,
) -> list[MealLog]:
    start, end = _day_bounds(start_date, end_date)
    result = await db.execute(
        select(MealLog)
        .options(
            selectinload(MealLog.recipe)
            .selectinload(Recipe.ingredients)
            .selectinload(RecipeIngredient.ingredient),
            selectinload(MealLog.recipe).selectinload(Recipe.dietary_tags),
        )
        .where(
            MealLog.client_id == client_id,
            MealLog.consumed_at >= start,
            MealLog.consumed_at < end,
        )
        .order_by(MealLog.consumed_at)
    )
    return list(result.scalars().all())


async def list_exercise_logs(
    db: AsyncSession,
    client_id: uuid.UUID,
    start_date: datetime.date,
    end_date: datetime.date,
) -> list[ExerciseLog]:
    start, end = _day_bounds(start_date, end_date)
    result = await db.execute(
        select(ExerciseLog)
        .options(selectinload(ExerciseLog.exercise))
        .where(
            ExerciseLog.client_id == client_id,
            ExerciseLog.completed_at >= start,
            ExerciseLog.completed_at < end,
        )
        .order_by(ExerciseLog.completed_at)
    )
    return list(result.scalars().all())
