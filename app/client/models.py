from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base, TimestampMixin, UUIDMixin

client_profile_dietary_tag = Table(
    "client_profile_dietary_tag",
    Base.metadata,
    Column(
        "client_profile_id",
        UUID(as_uuid=True),
        ForeignKey("client_profile.id"),
        primary_key=True,
    ),
    Column(
        "dietary_tag_id",
        UUID(as_uuid=True),
        ForeignKey("dietary_tag.id"),
        primary_key=True,
    ),
)


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
    cycle_length_days: Mapped[int] = mapped_column(Integer, default=28, nullable=False)
    period_length_days: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    last_period_start: Mapped[date | None] = mapped_column(Date, nullable=True)

    dietary_tags: Mapped[list["DietaryTag"]] = relationship(  # noqa: F821
        secondary=client_profile_dietary_tag
    )
    user: Mapped["User"] = relationship(  # noqa: F821
        back_populates="client_profile"
    )
    trainer: Mapped["TrainerProfile"] = relationship(  # noqa: F821
        back_populates="client_profiles"
    )

    @property
    def first_name(self) -> str | None:
        return self.user.first_name if self.user else None

    @property
    def last_name(self) -> str | None:
        return self.user.last_name if self.user else None

    @property
    def email(self) -> str | None:
        return self.user.email if self.user else None
