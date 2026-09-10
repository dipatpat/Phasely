import uuid
from datetime import date, time

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.trainer.models import TrainerAvailability, TrainerProfile


class TrainerProfileAlreadyExistsError(Exception):
    pass


async def get_trainer_profile_by_user_id(
    db: AsyncSession, user_id: uuid.UUID
) -> TrainerProfile | None:
    result = await db.execute(
        select(TrainerProfile).where(TrainerProfile.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_trainer_profile_by_id(
    db: AsyncSession, trainer_profile_id: uuid.UUID
) -> TrainerProfile | None:
    result = await db.execute(
        select(TrainerProfile)
        .options(selectinload(TrainerProfile.user))
        .where(TrainerProfile.id == trainer_profile_id)
    )
    return result.scalar_one_or_none()


async def create_trainer_profile(
    db: AsyncSession,
    user_id: uuid.UUID,
    bio: str | None = None,
    specialization: str | None = None,
) -> TrainerProfile:
    new_profile = TrainerProfile(
        user_id=user_id, bio=bio, specialization=specialization
    )
    try:
        db.add(new_profile)
        await db.commit()
        await db.refresh(new_profile)
        return new_profile
    except IntegrityError as e:
        await db.rollback()
        raise TrainerProfileAlreadyExistsError("Trainer profile already exists") from e


async def update_trainer_profile(
    db: AsyncSession,
    profile: TrainerProfile,
    bio: str | None = None,
    specialization: str | None = None,
) -> TrainerProfile:
    if bio is not None:
        profile.bio = bio
    if specialization is not None:
        profile.specialization = specialization
    await db.commit()
    await db.refresh(profile)
    return profile


async def create_availability_slot(
    db: AsyncSession,
    trainer_id: uuid.UUID,
    slot_date: date,
    slot_start: time,
    slot_end: time,
) -> TrainerAvailability:
    new_slot = TrainerAvailability(
        trainer_id=trainer_id,
        slot_date=slot_date,
        slot_start=slot_start,
        slot_end=slot_end,
        timezone="Europe/Warsaw",
        is_active=True,
    )
    db.add(new_slot)
    await db.commit()
    await db.refresh(new_slot)
    return new_slot


async def list_availability_slots(
    db: AsyncSession, trainer_id: uuid.UUID
) -> list[TrainerAvailability]:
    result = await db.execute(
        select(TrainerAvailability).where(TrainerAvailability.trainer_id == trainer_id)
    )
    return list(result.scalars().all())


async def get_availability_slot(
    db: AsyncSession, slot_id: uuid.UUID, trainer_id: uuid.UUID
) -> TrainerAvailability | None:
    result = await db.execute(
        select(TrainerAvailability).where(
            TrainerAvailability.id == slot_id,
            TrainerAvailability.trainer_id == trainer_id,
        )
    )
    return result.scalar_one_or_none()


async def update_availability_slot(
    db: AsyncSession,
    slot: TrainerAvailability,
    slot_date: date | None = None,
    slot_start: time | None = None,
    slot_end: time | None = None,
    is_active: bool | None = None,
) -> TrainerAvailability:
    if slot_date is not None:
        slot.slot_date = slot_date
    if slot_start is not None:
        slot.slot_start = slot_start
    if slot_end is not None:
        slot.slot_end = slot_end
    if is_active is not None:
        slot.is_active = is_active
    await db.commit()
    await db.refresh(slot)
    return slot


async def delete_availability_slot(db: AsyncSession, slot: TrainerAvailability) -> None:
    await db.delete(slot)
    await db.commit()


async def list_all_trainer_profiles(db: AsyncSession) -> list[TrainerProfile]:
    result = await db.execute(select(TrainerProfile))
    return list(result.scalars().all())
