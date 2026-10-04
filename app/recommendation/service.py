import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CyclePhase
from app.log.models import PeriodLog

LUTEAL_LENGTH_DAYS = 14
OVULATION_WINDOW_DAYS = 3


def calculate_cycle_phase(
    last_period_start: date,
    cycle_length_days: int,
    period_length_days: int,
    target_date: date,
) -> CyclePhase:
    day_of_cycle = ((target_date - last_period_start).days % cycle_length_days) + 1
    luteal_start_day = cycle_length_days - LUTEAL_LENGTH_DAYS + 1
    ovulatory_start_day = luteal_start_day - OVULATION_WINDOW_DAYS

    if day_of_cycle <= period_length_days:
        return CyclePhase.menstrual
    elif day_of_cycle < ovulatory_start_day:
        return CyclePhase.follicular
    elif day_of_cycle < luteal_start_day:
        return CyclePhase.ovulatory
    else:
        return CyclePhase.luteal


def calculate_cycle_length(period_starts: list[date]) -> int | None:
    if len(period_starts) < 2:
        return None
    sorted_starts = sorted(period_starts)
    return (sorted_starts[-1] - sorted_starts[-2]).days


async def create_period_log(
    db: AsyncSession, client_id: uuid.UUID, period_start_date: date
) -> PeriodLog:
    new_entry = PeriodLog(client_id=client_id, period_start_date=period_start_date)
    db.add(new_entry)
    await db.commit()
    await db.refresh(new_entry)
    return new_entry


async def get_period_start_dates(db: AsyncSession, client_id: uuid.UUID) -> list[date]:
    result = await db.execute(
        select(PeriodLog.period_start_date).where(PeriodLog.client_id == client_id)
    )
    return list(result.scalars().all())
