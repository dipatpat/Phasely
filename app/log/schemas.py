import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.core.enums import CyclePhase


class DailyLogCreate(BaseModel):
    log_date: date
    cycle_phase: CyclePhase
    hours_of_sleep: Decimal | None = None
    energy_level: int | None = None


class DailyLogPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    client_id: uuid.UUID
    log_date: date
    cycle_phase: CyclePhase
    hours_of_sleep: Decimal | None
    energy_level: int | None
    created_at: datetime
