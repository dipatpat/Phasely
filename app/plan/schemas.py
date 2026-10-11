import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import CyclePhase, DifficultyLevel, MealType
from app.exercise.schemas import ExercisePublic
from app.recipe.schemas import RecipePublic


class NutritionPlanRecipePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    recipe: RecipePublic
    meal_type: MealType
    cycle_phase: CyclePhase


class NutritionPlanRecipeCreate(BaseModel):
    recipe_id: uuid.UUID
    meal_type: MealType
    cycle_phase: CyclePhase


class NutritionPlanCreate(BaseModel):
    client_id: uuid.UUID
    title: str
    recipes: list[NutritionPlanRecipeCreate] = []


class NutritionPlanUpdate(BaseModel):
    title: str | None = None
    is_active: bool | None = None
    recipes: list[NutritionPlanRecipeCreate] | None = None


class NutritionPlanPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    client_id: uuid.UUID
    trainer_id: uuid.UUID
    title: str
    is_active: bool
    recipes: list[NutritionPlanRecipePublic]
    created_at: datetime
    updated_at: datetime


class TrainingPlanExerciseCreate(BaseModel):
    exercise_id: uuid.UUID
    cycle_phase: CyclePhase
    day_of_week: int = Field(ge=1, le=7)
    sets: int | None = Field(default=None, ge=1)
    reps: int | None = Field(default=None, ge=1)
    duration_seconds: int | None = Field(default=None, ge=1)
    weight_kg: Decimal | None = Field(default=None, ge=0)
    rest_seconds: int | None = Field(default=None, ge=0)
    difficulty_level: DifficultyLevel | None = None


class TrainingPlanExercisePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    exercise: ExercisePublic
    cycle_phase: CyclePhase
    day_of_week: int
    sets: int | None = None
    reps: int | None = None
    duration_seconds: int | None = None
    weight_kg: Decimal | None = None
    rest_seconds: int | None = None
    difficulty_level: DifficultyLevel | None = None


class TrainingPlanCreate(BaseModel):
    client_id: uuid.UUID
    title: str
    exercises: list[TrainingPlanExerciseCreate] = []


class TrainingPlanUpdate(BaseModel):
    title: str | None = None
    is_active: bool | None = None
    exercises: list[TrainingPlanExerciseCreate] | None = None


class TrainingPlanPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    client_id: uuid.UUID
    trainer_id: uuid.UUID
    title: str
    is_active: bool
    exercises: list[TrainingPlanExercisePublic]
    created_at: datetime
    updated_at: datetime
