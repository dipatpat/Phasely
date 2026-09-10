import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.client.models import ClientProfile
from app.trainer.service import get_trainer_profile_by_id


class ClientProfileAlreadyExistsError(Exception):
    pass


class TrainerNotFoundError(Exception):
    pass


async def get_client_profile_by_user_id(
    db: AsyncSession, user_id: uuid.UUID
) -> ClientProfile | None:
    result = await db.execute(
        select(ClientProfile).where(ClientProfile.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_client_profile(
    db: AsyncSession,
    user_id: uuid.UUID,
    trainer_id: uuid.UUID,
    body_fat_percentage: Decimal | None = None,
    fitness_goal: str | None = None,
    cycle_length_days: int | None = None,
    period_length_days: int | None = None,
    last_period_start: date | None = None,
) -> ClientProfile:
    trainer = await get_trainer_profile_by_id(db, trainer_id)
    if trainer is None:
        raise TrainerNotFoundError()
    new_profile = ClientProfile(
        user_id=user_id,
        trainer_id=trainer_id,
        body_fat_percentage=body_fat_percentage,
        fitness_goal=fitness_goal,
        cycle_length_days=cycle_length_days,
        period_length_days=period_length_days,
        last_period_start=last_period_start,
        onboarded_at=datetime.now(UTC),
    )

    try:
        db.add(new_profile)
        await db.commit()
        await db.refresh(new_profile)
        return new_profile
    except IntegrityError as e:
        await db.rollback()
        raise ClientProfileAlreadyExistsError("Client profile already exists") from e


async def update_client_profile(
    db: AsyncSession,
    profile: ClientProfile,
    body_fat_percentage: Decimal | None = None,
    fitness_goal: str | None = None,
    cycle_length_days: int | None = None,
    period_length_days: int | None = None,
    last_period_start: date | None = None,
) -> ClientProfile:
    if body_fat_percentage is not None:
        profile.body_fat_percentage = body_fat_percentage
    if fitness_goal is not None:
        profile.fitness_goal = fitness_goal
    if cycle_length_days is not None:
        profile.cycle_length_days = cycle_length_days
    if period_length_days is not None:
        profile.period_length_days = period_length_days
    if last_period_start is not None:
        profile.last_period_start = last_period_start
    await db.commit()
    await db.refresh(profile)
    return profile


async def get_client_profile_by_id(
    db: AsyncSession, client_profile_id: uuid.UUID, trainer_id: uuid.UUID
) -> ClientProfile | None:
    result = await db.execute(
        select(ClientProfile).where(
            ClientProfile.id == client_profile_id,
            ClientProfile.trainer_id == trainer_id,
        )
    )
    return result.scalar_one_or_none()


async def list_clients_by_trainer_id(
    db: AsyncSession, trainer_id: uuid.UUID
) -> list[ClientProfile]:
    result = await db.execute(
        select(ClientProfile)
        .options(selectinload(ClientProfile.user))
        .where(ClientProfile.trainer_id == trainer_id)
    )

    return list(result.scalars().all())
