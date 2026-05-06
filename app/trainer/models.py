from datetime import time

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base, TimestampMixin, UUIDMixin


class TrainerProfile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "trainer_profile"

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, unique=True
    )
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    specialization: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship(  # noqa: F821
        back_populates="trainer_profile"
    )
    availability: Mapped[list["TrainerAvailability"]] = relationship(
        back_populates="trainer"
    )
    client_profiles: Mapped[list["ClientProfile"]] = relationship(  # noqa: F821
        back_populates="trainer"
    )


class TrainerAvailability(UUIDMixin, Base):
    __tablename__ = "trainer_availability"

    trainer_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trainer_profile.id"), nullable=False
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    slot_start: Mapped[time] = mapped_column(Time, nullable=False)
    slot_end: Mapped[time] = mapped_column(Time, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    trainer: Mapped["TrainerProfile"] = relationship(back_populates="availability")
