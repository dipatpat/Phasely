import uuid
from decimal import Decimal

from sqlalchemy import Boolean, Enum, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base, TimestampMixin, UUIDMixin
from app.core.enums import CyclePhase, MealType


class NutritionPlan(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "nutrition_plan"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("client_profile.id"), nullable=False
    )
    trainer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trainer_profile.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    recipes: Mapped[list["NutritionPlanRecipe"]] = relationship(
        back_populates="nutrition_plan", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index(
            "ix_nutrition_plan_client_active",
            "client_id",
            unique=True,
            postgresql_where="is_active = true",
        ),
    )


class TrainingPlan(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "training_plan"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("client_profile.id"), nullable=False
    )
    trainer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trainer_profile.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    exercises: Mapped[list["TrainingPlanExercise"]] = relationship(
        back_populates="training_plan", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index(
            "ix_training_plan_client_active",
            "client_id",
            unique=True,
            postgresql_where="is_active = true",
        ),
    )


class NutritionPlanRecipe(Base):
    __tablename__ = "nutrition_plan_recipe"

    nutrition_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nutrition_plan.id"), primary_key=True
    )
    recipe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recipe.id"), primary_key=True
    )
    meal_type: Mapped[MealType] = mapped_column(
        Enum(MealType), primary_key=True, nullable=False
    )
    cycle_phase: Mapped[CyclePhase] = mapped_column(
        Enum(CyclePhase), primary_key=True, nullable=False
    )

    nutrition_plan: Mapped["NutritionPlan"] = relationship(back_populates="recipes")
    recipe: Mapped["Recipe"] = relationship()  # noqa: F821


class TrainingPlanExercise(Base):
    __tablename__ = "training_plan_exercise"

    training_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("training_plan.id"), primary_key=True
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exercise.id"), primary_key=True
    )
    cycle_phase: Mapped[CyclePhase] = mapped_column(
        Enum(CyclePhase), primary_key=True, nullable=False
    )
    day_of_week: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    sets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    rest_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difficulty_level: Mapped[str | None] = mapped_column(String(50), nullable=True)

    training_plan: Mapped["TrainingPlan"] = relationship(back_populates="exercises")
    exercise: Mapped["Exercise"] = relationship()  # noqa: F821
