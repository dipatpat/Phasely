import uuid
from datetime import date, datetime, time

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.client.models import ClientProfile
from app.client.service import get_client_profile_by_user_id
from app.core.enums import UserRole
from app.session.models import Session, SessionStatus
from app.trainer.models import TrainerAvailability, TrainerProfile
from app.trainer.service import get_trainer_profile_by_user_id
from app.user.models import User


class InvalidTransitionError(Exception):
    pass


class SlotUnavailableError(Exception):
    pass


async def get_session_by_id(db: AsyncSession, session_id: uuid.UUID) -> Session | None:
    result = await db.execute(
        select(Session)
        .options(
            selectinload(Session.trainer).selectinload(TrainerProfile.user),
            selectinload(Session.client).selectinload(ClientProfile.user),
        )
        .where(Session.id == session_id)
    )
    return result.scalar_one_or_none()


async def book_session(
    db: AsyncSession,
    client_id: uuid.UUID,
    trainer_id: uuid.UUID,
    slot_date: date,
    slot_start: time,
    notes: str | None = None,
) -> Session:
    free_slot = await is_slot_available(
        db, trainer_id, slot_date=slot_date, slot_start=slot_start
    )
    if not free_slot:
        raise SlotUnavailableError
    scheduled_at = datetime.combine(slot_date, slot_start)
    new_session = Session(
        client_id=client_id,
        trainer_id=trainer_id,
        scheduled_at=scheduled_at,
        notes=notes,
    )
    try:
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
    except IntegrityError as e:
        await db.rollback()
        raise SlotUnavailableError("Slot is already booked") from e
    return new_session


async def confirm_session(db: AsyncSession, session: Session) -> Session:
    if session.status != SessionStatus.pending:
        raise InvalidTransitionError
    session.status = SessionStatus.confirmed
    await db.commit()
    await db.refresh(session)
    return session


async def complete_session(db: AsyncSession, session: Session) -> Session:
    if session.status != SessionStatus.confirmed:
        raise InvalidTransitionError
    session.status = SessionStatus.completed
    await db.commit()
    await db.refresh(session)
    return session


async def cancel_session(
    db: AsyncSession, session: Session, reason: str | None = None
) -> Session:
    if session.status not in (SessionStatus.pending, SessionStatus.confirmed):
        raise InvalidTransitionError
    session.status = SessionStatus.cancelled
    session.cancellation_reason = reason
    await db.commit()
    await db.refresh(session)
    return session


async def is_slot_available(
    db: AsyncSession, trainer_id: uuid.UUID, slot_date: date, slot_start: time
) -> bool:
    scheduled_at = datetime.combine(slot_date, slot_start)
    availability = await db.execute(
        select(TrainerAvailability).where(
            TrainerAvailability.slot_date == slot_date,
            TrainerAvailability.slot_start == slot_start,
            TrainerAvailability.is_active.is_(True),
        )
    )
    if availability.scalar_one_or_none() is None:
        return False
    is_booked_slot = await db.execute(
        select(Session).where(
            Session.trainer_id == trainer_id,
            Session.scheduled_at == scheduled_at,
        )
    )

    return is_booked_slot.scalar_one_or_none() is None


async def list_available_slots(
    db: AsyncSession, trainer_id: uuid.UUID, date_target: datetime
) -> list[TrainerAvailability]:
    results = await db.execute(
        select(TrainerAvailability).where(
            TrainerAvailability.trainer_id == trainer_id,
            TrainerAvailability.slot_date == date_target,
            TrainerAvailability.is_active.is_(True),
        )
    )
    slots_on_day = results.scalars().all()
    available_slots = []
    for slot in slots_on_day:
        available_slot = await is_slot_available(
            db, trainer_id, slot.slot_date, slot.slot_start
        )
        if available_slot:
            available_slots.append(slot)
    return available_slots


async def list_session_for_user(db: AsyncSession, user: User) -> list[Session]:
    if user.role == UserRole.trainer:
        trainer_profile = await get_trainer_profile_by_user_id(db, user.id)
        if trainer_profile is None:
            return []
        allowed_user = Session.trainer_id == trainer_profile.id
    else:
        client_profile = await get_client_profile_by_user_id(db, user.id)
        if client_profile is None:
            return []
        allowed_user = Session.client_id == client_profile.id
    results = await db.execute(
        select(Session)
        .options(
            selectinload(Session.trainer).selectinload(TrainerProfile.user),
            selectinload(Session.client).selectinload(ClientProfile.user),
        )
        .where(allowed_user)
        .order_by(Session.scheduled_at)
    )
    booked_sessions = results.scalars().all()
    return list(booked_sessions)
