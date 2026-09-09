import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ClientProfileCreate(BaseModel):
    trainer_id: uuid.UUID
    body_fat_percentage: Decimal | None = None
    fitness_goal: str | None = None
    cycle_length_days: int = 28
    period_length_days: int = 5
    last_period_start: date | None = None


class ClientProfileUpdate(BaseModel):
    body_fat_percentage: Decimal | None = None
    fitness_goal: str | None = None
    cycle_length_days: int | None = None
    period_length_days: int | None = None
    last_period_start: date | None = None


class ClientProfilePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    trainer_id: uuid.UUID
    body_fat_percentage: Decimal | None
    fitness_goal: str | None
    onboarded_at: datetime | None
    cycle_length_days: int
    period_length_days: int
    last_period_start: date | None
    created_at: datetime
    updated_at: datetime
