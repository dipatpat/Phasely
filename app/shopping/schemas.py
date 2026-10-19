import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.core.enums import CyclePhase, MealType


class PlannedMeal(BaseModel):
    meal_type: MealType
    recipe_id: uuid.UUID
    recipe_name: str


class ShoppingListDay(BaseModel):
    date: date
    cycle_phase: CyclePhase | None
    meals: list[PlannedMeal]


class ShoppingListItem(BaseModel):
    ingredient: str
    quantity: Decimal
    unit: str


class ShoppingListPublic(BaseModel):
    week_start: date
    week_end: date
    days: list[ShoppingListDay]
    unpredictable_dates: list[date]
    items: list[ShoppingListItem]
