import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_trainer
from app.core.database import get_db
from app.exercise.schemas import ExerciseCreate, ExercisePublic, ExerciseUpdate
from app.exercise.service import (
    ExerciseAlreadyExistsError,
    ExerciseInUseError,
    ExerciseNotFound,
    create_exercise,
    delete_exercise,
    get_exercise_by_id,
    list_exercises,
    update_exercise,
)
from app.user.models import User

router = APIRouter(prefix="/exercise", tags=["exercise"])


@router.post(
    "/create", response_model=ExercisePublic, status_code=status.HTTP_201_CREATED
)
async def handle_create_exercise(
    data: ExerciseCreate,
    user: User = Depends(require_trainer),
    db: AsyncSession = Depends(get_db),
):
    try:
        new_exercise = await create_exercise(db, data.name, data.description)
    except ExerciseAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Exercise already exists",
        ) from e

    return new_exercise


@router.patch("/update", response_model=ExercisePublic, status_code=status.HTTP_200_OK)
async def handle_update_exercise(
    exercise_id: uuid.UUID,
    data: ExerciseUpdate,
    user: User = Depends(require_trainer),
    db: AsyncSession = Depends(get_db),
):
    try:
        new_exercise = await update_exercise(
            db, exercise_id, data.name, data.description
        )
    except ExerciseAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Exercise already exists",
        ) from e
    except ExerciseNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found",
        ) from e

    return new_exercise


@router.delete("/remove", status_code=status.HTTP_204_NO_CONTENT)
async def handle_delete_exercise(
    exercise_id: uuid.UUID,
    user: User = Depends(require_trainer),
    db: AsyncSession = Depends(get_db),
):
    try:
        await delete_exercise(db, exercise_id)
    except ExerciseNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found",
        ) from e
    except ExerciseInUseError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Exercise is used in a plan",
        ) from e

    return None


@router.get("/", response_model=list[ExercisePublic], status_code=status.HTTP_200_OK)
async def handle_get_exercises(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await list_exercises(db)
    return result


@router.get("/by_id", response_model=ExercisePublic, status_code=status.HTTP_200_OK)
async def handle_get_exercises_by_id(
    exercise_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await get_exercise_by_id(db, exercise_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found",
        )
    return result
