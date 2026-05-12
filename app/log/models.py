import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base, TimestampMixin, UUIDMixin
from app.core.enums import CyclePhase, MealType


class DailyLog(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "daily_log"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("client_profile.id"), nullable=False
    )
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    cycle_phase: Mapped[CyclePhase] = mapped_column(Enum(CyclePhase), nullable=False)
    hours_of_sleep: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)
    energy_level: Mapped[int | None] = mapped_column(Integer, nullable=True)

    client: Mapped["ClientProfile"] = relationship()  # noqa: F821

    __table_args__ = (
        UniqueConstraint("client_id", "log_date", name="uq_daily_log_client_date"),
    )


class MealLog(UUIDMixin, Base):
    __tablename__ = "meal_log"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("client_profile.id"), nullable=False
    )
    recipe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recipe.id"), nullable=False
    )
    meal_type: Mapped[MealType] = mapped_column(Enum(MealType), nullable=False)
    consumed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    portion_quantity: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    portion_unit: Mapped[str] = mapped_column(String(50), nullable=False)

    client: Mapped["ClientProfile"] = relationship()  # noqa: F821
    recipe: Mapped["Recipe"] = relationship()  # noqa: F821


class ExerciseLog(UUIDMixin, Base):
    __tablename__ = "exercise_log"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("client_profile.id"), nullable=False
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exercise.id"), nullable=False
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    client: Mapped["ClientProfile"] = relationship()  # noqa: F821
    exercise: Mapped["Exercise"] = relationship()  # noqa: F821
