import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.core.enums import MealType


class IngredientCreate(BaseModel):
    name: str
    quantity: Decimal
    unit: str


class IngredientPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    quantity: Decimal
    unit: str


class DietaryTagPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str


class RecipeCreate(BaseModel):
    name: str
    meal_type: MealType
    protein: Decimal
    carbs: Decimal
    fat: Decimal
    calories: int
    serving_size: str
    preparation_notes: str | None = None
    ingredients: list[IngredientCreate]
    dietary_tag_names: list[str] = []


class RecipeUpdate(BaseModel):
    name: str | None = None
    meal_type: MealType | None = None
    protein: Decimal | None = None
    carbs: Decimal | None = None
    fat: Decimal | None = None
    calories: int | None = None
    serving_size: str | None = None
    preparation_notes: str | None = None
    ingredients: list[IngredientCreate] | None = None
    dietary_tag_names: list[str] | None = None


class RecipePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    meal_type: MealType
    protein: Decimal
    carbs: Decimal
    fat: Decimal
    calories: int
    serving_size: str
    preparation_notes: str | None = None
    ingredients: list[IngredientPublic]
    dietary_tags: list[DietaryTagPublic]
    created_at: datetime
    updated_at: datetime
