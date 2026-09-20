import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.client.schemas import ClientProfilePublic
from app.session.models import SessionStatus
from app.trainer.schemas import TrainerProfilePublic


class SessionCreateByClient(BaseModel):
    scheduled_at: datetime
    notes: str | None = None


class SessionCreateByTrainer(BaseModel):
    client_id: uuid.UUID
    scheduled_at: datetime
    notes: str | None = None


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
