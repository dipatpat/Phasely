from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base, TimestampMixin, UUIDMixin
from app.core.enums import UserRole


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "user"

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    trainer_profile: Mapped["TrainerProfile"] = relationship(  # noqa: F821
        back_populates="user", uselist=False
    )
    client_profile: Mapped["ClientProfile"] = relationship(  # noqa: F821
        back_populates="user", uselist=False
    )

    __table_args__ = (
        Index(
            "ix_user_email_active",
            "email",
            unique=True,
            postgresql_where="is_active = true",
        ),
    )
