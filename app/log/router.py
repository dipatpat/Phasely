from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_client
from app.client.service import get_client_profile_by_user_id
from app.core.database import get_db
from app.exercise.service import ExerciseNotFound
from app.log.schemas import (
    DailyLogCreate,
    DailyLogPublic,
    ExerciseLogCreate,
    ExerciseLogPublic,
    MealLogCreate,
    MealLogPublic,
)
from app.log.service import (
    DailyLogAlreadyExistsError,
    create_daily_log,
    create_exercise_log,
    create_meal_log,
)
from app.recipe.service import RecipeNotFoundError
from app.user.models import User

router = APIRouter(prefix="/log", tags=["log"])


@router.post(
    "/daily/create", response_model=DailyLogPublic, status_code=status.HTTP_201_CREATED
)
async def handle_create_daily_log(
    data: DailyLogCreate,
    user: User = Depends(require_client),
    db: AsyncSession = Depends(get_db),
):
    client_profile = await get_client_profile_by_user_id(db, user.id)
    if client_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No client profile found"
        )
    try:
        new_log = await create_daily_log(
            db,
            client_profile.id,
            data.log_date,
            data.cycle_phase,
            data.hours_of_sleep,
            data.energy_level,
        )
    except DailyLogAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Already logged for this date"
        ) from e
    return new_log


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
