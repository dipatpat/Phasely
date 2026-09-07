import uuid
from datetime import datetime, time

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
    day_of_week: int = Field(
        ..., ge=0, le=6, description="Day of the week (0=Monday, 6=Sunday)"
    )
    slot_start: time = Field(..., description="Start time in HH:MM format")
    slot_end: time = Field(..., description="End time in HH:MM format")


class TrainerAvailabilityUpdate(BaseModel):
    day_of_week: int | None = Field(
        None, ge=0, le=6, description="Day of the week (0=Monday, 6=Sunday)"
    )
    slot_start: time | None = Field(None, description="Start time in HH:MM format")
    slot_end: time | None = Field(None, description="End time in HH:MM format")
    is_active: bool | None = Field(
        None, description="Indicates if the availability slot is active"
    )


class TrainerAvailabilityPublic(BaseModel):
    id: uuid.UUID
    trainer_id: uuid.UUID
    day_of_week: int
    slot_start: time
    slot_end: time
    timezone: str
    is_active: bool
    model_config = ConfigDict(from_attributes=True)
