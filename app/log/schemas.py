import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.core.enums import CyclePhase, MealType
from app.exercise.schemas import ExercisePublic
from app.recipe.schemas import RecipePublic


class DailyLogCreate(BaseModel):
    log_date: date
    period_started_today: bool = False
    cycle_phase: CyclePhase | None = None
    hours_of_sleep: Decimal | None = None
    energy_level: int | None = None


class DailyLogPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    client_id: uuid.UUID
    log_date: date
    cycle_phase: CyclePhase
    hours_of_sleep: Decimal | None
    energy_level: int | None
    created_at: datetime


class MealLogCreate(BaseModel):
    recipe_id: uuid.UUID
    meal_type: MealType
    consumed_at: datetime
    portion_quantity: Decimal
    portion_unit: str


class MealLogPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    client_id: uuid.UUID
    recipe: RecipePublic
    meal_type: MealType
    consumed_at: datetime
    portion_quantity: Decimal
    portion_unit: str


class ExerciseLogCreate(BaseModel):
    exercise_id: uuid.UUID
    completed_at: datetime
    notes: str | None = None


class ExerciseLogPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    client_id: uuid.UUID
    exercise: ExercisePublic
    completed_at: datetime
    notes: str | None
