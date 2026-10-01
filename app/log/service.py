import datetime
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CyclePhase
from app.log.models import DailyLog


class DailyLogAlreadyExistsError(Exception):
    pass


async def create_daily_log(
    db: AsyncSession,
    client_id: uuid.UUID,
    log_date: datetime.date,
    cycle_phase: CyclePhase,
    hours_of_sleep: Decimal | None,
    energy_level: int | None,
) -> DailyLog:
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
    await trigger_recommendation(
        client_id, log_date, cycle_phase, hours_of_sleep, energy_level
    )
    return new_log


async def trigger_recommendation(
    client_id: uuid.UUID,
    log_date: datetime.date,
    cycle_phase: CyclePhase,
    hours_of_sleep: Decimal | None,
    energy_level: int | None,
):
    pass


async def get_daily_log_by_id(db: AsyncSession, log_id: uuid.UUID) -> DailyLog | None:
    result = await db.execute(select(DailyLog).where(DailyLog.id == log_id))
    return result.scalar_one_or_none()
