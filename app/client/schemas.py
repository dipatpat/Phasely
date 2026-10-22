import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.log.schemas import DailyLogPublic

CycleLengthDays = Annotated[int, Field(ge=21, le=45)]
PeriodLengthDays = Annotated[int, Field(ge=1, le=10)]


class ClientProfileCreate(BaseModel):
    trainer_id: uuid.UUID
    body_fat_percentage: Decimal | None = None
    fitness_goal: str | None = None
    cycle_length_days: CycleLengthDays = 28
    period_length_days: PeriodLengthDays = 5
    last_period_start: date | None = None


class ClientProfileUpdate(BaseModel):
    body_fat_percentage: Decimal | None = None
    fitness_goal: str | None = None
    cycle_length_days: CycleLengthDays | None = None
    period_length_days: PeriodLengthDays | None = None
    last_period_start: date | None = None


class ClientProfilePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    first_name: str | None
    last_name: str | None
    email: str | None
    body_fat_percentage: Decimal | None
    fitness_goal: str | None
    onboarded_at: datetime | None
    cycle_length_days: int
    period_length_days: int
    last_period_start: date | None
    created_at: datetime
    updated_at: datetime


class ClientOverview(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    client: ClientProfilePublic
    today_log: DailyLogPublic | None
    last_log_date: date | None
    has_nutrition_plan: bool
    has_training_plan: bool
