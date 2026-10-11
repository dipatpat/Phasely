import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.client.schemas import ClientProfilePublic
from app.core.config import APP_TZ
from app.session.models import SessionStatus
from app.trainer.schemas import TrainerProfilePublic


def to_app_wall_time(value: datetime) -> datetime:
    # Slots are stored as local wall-clock times, so offset-aware input is
    # converted to the app timezone before its date and time are matched
    if value.tzinfo is not None:
        value = value.astimezone(APP_TZ)
    return value.replace(tzinfo=None)


class SessionCreateByClient(BaseModel):
    scheduled_at: datetime
    notes: str | None = None

    _normalize_scheduled_at = field_validator("scheduled_at")(to_app_wall_time)


class SessionCreateByTrainer(BaseModel):
    client_id: uuid.UUID
    scheduled_at: datetime
    notes: str | None = None

    _normalize_scheduled_at = field_validator("scheduled_at")(to_app_wall_time)


class SessionUpdate(BaseModel):
    notes: str | None = None


class SessionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    client: ClientProfilePublic
    trainer: TrainerProfilePublic
    scheduled_at: datetime
    status: SessionStatus
    notes: str | None
    duration_minutes: int
    cancellation_reason: str | None = None


class SessionCancel(BaseModel):
    cancellation_reason: str | None = None
