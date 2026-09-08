import uuid
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field


class TrainerProfileCreate(BaseModel):
    bio: str | None = None
    specialization: str | None = None


class TrainerProfileUpdate(BaseModel):
    bio: str | None = None
    specialization: str | None = None


class TrainerProfilePublic(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    bio: str | None = None
    specialization: str | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TrainerAvailabilityCreate(BaseModel):
    slot_date: date = Field(..., description="Date of the availability slot")
    slot_start: time = Field(..., description="Start time in HH:MM format")
    slot_end: time = Field(..., description="End time in HH:MM format")


class TrainerAvailabilityUpdate(BaseModel):
    slot_date: date | None = Field(None, description="Date of the availability slot")
    slot_start: time | None = Field(None, description="Start time in HH:MM format")
    slot_end: time | None = Field(None, description="End time in HH:MM format")
    is_active: bool | None = Field(
        None, description="Indicates if the availability slot is active"
    )


class TrainerAvailabilityPublic(BaseModel):
    id: uuid.UUID
    trainer_id: uuid.UUID
    slot_date: date
    slot_start: time
    slot_end: time
    timezone: str
    is_active: bool
    model_config = ConfigDict(from_attributes=True)
