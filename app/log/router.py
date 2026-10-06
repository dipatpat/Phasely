from datetime import date

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_client
from app.client.service import get_client_profile_by_user_id
from app.core.database import get_db
from app.core.redis import get_redis
from app.exercise.service import ExerciseNotFound
from app.log.schemas import (
    DailyLogCreate,
    DailyLogWithRecommendations,
    ExerciseLogCreate,
    ExerciseLogPublic,
    MealLogCreate,
    MealLogPublic,
)
from app.log.service import (
    DailyLogAlreadyExistsError,
    InsufficientCycleDataError,
    create_daily_log,
    create_exercise_log,
    create_meal_log,
    get_daily_log_by_client_and_date,
    trigger_recommendation,
)
from app.recipe.service import RecipeNotFoundError
from app.user.models import User

router = APIRouter(prefix="/log", tags=["log"])


@router.post(
    "/daily/create",
    response_model=DailyLogWithRecommendations,
    status_code=status.HTTP_201_CREATED,
)
async def handle_create_daily_log(
    data: DailyLogCreate,
    user: User = Depends(require_client),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    client_profile = await get_client_profile_by_user_id(db, user.id)
    if client_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No client profile found"
        )
    try:
        new_log, recipes, exercises = await create_daily_log(
            db,
            client_profile.id,
            data.log_date,
            data.period_started_today,
            data.cycle_phase,
            data.hours_of_sleep,
            data.energy_level,
            redis,
        )
    except DailyLogAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Already logged for this date"
        ) from e
    except InsufficientCycleDataError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough cycle data to calculate phase",
        ) from e
    return DailyLogWithRecommendations(
        daily_log=new_log,
        recommended_recipes=recipes,
        recommended_exercises=exercises,
    )


@router.post(
    "/meal/create", response_model=MealLogPublic, status_code=status.HTTP_201_CREATED
)
async def handle_create_meal_log(
    data: MealLogCreate,
    user: User = Depends(require_client),
    db: AsyncSession = Depends(get_db),
):
    client_profile = await get_client_profile_by_user_id(db, user.id)
    if client_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No client profile found"
        )
    try:
        new_log = await create_meal_log(
            db,
            client_profile.id,
            data.recipe_id,
            data.meal_type,
            data.consumed_at,
            data.portion_quantity,
            data.portion_unit,
        )
    except RecipeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
        ) from e
    return new_log


@router.post(
    "/exercise/create",
    response_model=ExerciseLogPublic,
    status_code=status.HTTP_201_CREATED,
)
async def handle_create_exercise_log(
    data: ExerciseLogCreate,
    user: User = Depends(require_client),
    db: AsyncSession = Depends(get_db),
):
    client_profile = await get_client_profile_by_user_id(db, user.id)
    if client_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No client profile found"
        )
    try:
        new_log = await create_exercise_log(
            db, client_profile.id, data.exercise_id, data.completed_at, data.notes
        )
    except ExerciseNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found"
        ) from e
    return new_log


@router.get(
    "/daily/today",
    response_model=DailyLogWithRecommendations,
    status_code=status.HTTP_200_OK,
)
async def handle_get_today_recommendations(
    user: User = Depends(require_client),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    client_profile = await get_client_profile_by_user_id(db, user.id)
    if client_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No client profile found"
        )
    today = date.today()
    daily_log = await get_daily_log_by_client_and_date(db, client_profile.id, today)
    if daily_log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No log for today yet"
        )
    recipes, exercises = await trigger_recommendation(
        db,
        redis,
        client_profile.id,
        today,
        daily_log.cycle_phase,
        daily_log.energy_level,
    )
    return DailyLogWithRecommendations(
        daily_log=daily_log,
        recommended_recipes=recipes,
        recommended_exercises=exercises,
    )
