import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exercise.models import Exercise


class ExerciseAlreadyExistsError(Exception):
    pass


class ExerciseNotFound(Exception):
    pass


class ExerciseInUseError(Exception):
    pass


async def create_exercise(
    db: AsyncSession, name: str, description: str | None = None
) -> Exercise:
    new_exercise = Exercise(name=name, description=description)
    try:
        db.add(new_exercise)
        await db.commit()
        await db.refresh(new_exercise)
    except IntegrityError as e:
        await db.rollback()
        raise ExerciseAlreadyExistsError("Exercise already exists") from e
    return new_exercise


async def list_exercises(db: AsyncSession) -> list[Exercise]:
    results = await db.execute(select(Exercise))
    return list(results.scalars().all())


async def get_exercise_by_id(
    db: AsyncSession, exercise_id: uuid.UUID
) -> Exercise | None:
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    return result.scalar_one_or_none()


async def update_exercise(
    db: AsyncSession,
    exercise_id: uuid.UUID,
    name: str | None = None,
    description: str | None = None,
) -> Exercise:
    result = await get_exercise_by_id(db, exercise_id)
    if result is None:
        raise ExerciseNotFound("Exercise not found")
    if name is not None:
        result.name = name
    if description is not None:
        result.description = description
    try:
        await db.commit()
        await db.refresh(result)
    except IntegrityError as e:
        await db.rollback()
        raise ExerciseAlreadyExistsError("Exercise already exists") from e

    return result


async def delete_exercise(db: AsyncSession, exercise_id: uuid.UUID) -> None:
    result = await get_exercise_by_id(db, exercise_id)
    if result is None:
        raise ExerciseNotFound("Exercise not found")
    try:
        await db.delete(result)
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise ExerciseInUseError("Exercise is used in a plan") from e

    return None
