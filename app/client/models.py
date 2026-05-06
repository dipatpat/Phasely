from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base, TimestampMixin, UUIDMixin


class ClientProfile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "client_profile"

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, unique=True
    )
    trainer_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trainer_profile.id"), nullable=False
    )
    body_fat_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    fitness_goal: Mapped[str | None] = mapped_column(String(255), nullable=True)
    onboarded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship(  # noqa: F821
        back_populates="client_profile"
    )
    trainer: Mapped["TrainerProfile"] = relationship(  # noqa: F821
        back_populates="client_profiles"
    )
