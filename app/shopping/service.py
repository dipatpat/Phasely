import uuid
from collections import Counter, defaultdict
from datetime import date, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CyclePhase, MealType
from app.log.models import DailyLog
from app.plan.models import NutritionPlan, NutritionPlanRecipe
from app.recipe.models import Ingredient, Recipe, RecipeIngredient
from app.recommendation.service import get_cycle_parameters


async def generate_shopping_list(
    db: AsyncSession, client_id: uuid.UUID, week_start: date
) -> dict:
    week_dates = [week_start + timedelta(days=offset) for offset in range(7)]
    week_end = week_dates[-1]

    phases_by_date = await _get_logged_phases(db, client_id, week_start, week_end)
    if len(phases_by_date) < len(week_dates):
        cycle_parameters = await get_cycle_parameters(db, client_id)
        if cycle_parameters is not None:
            for day in week_dates:
                phases_by_date.setdefault(day, cycle_parameters.phase_on(day))

    options = await _get_recipe_options(db, client_id)

    phase_occurrence: Counter[CyclePhase] = Counter()
    servings_by_recipe: Counter[uuid.UUID] = Counter()
    days = []
    for day in week_dates:
        phase = phases_by_date.get(day)
        meals = []
        if phase is not None:
            occurrence = phase_occurrence[phase]
            phase_occurrence[phase] += 1
            for meal_type in MealType:
                choices = options.get((phase, meal_type))
                if not choices:
                    continue
                recipe_id, recipe_name = choices[occurrence % len(choices)]
                servings_by_recipe[recipe_id] += 1
                meals.append(
                    {
                        "meal_type": meal_type.value,
                        "recipe_id": str(recipe_id),
                        "recipe_name": recipe_name,
                    }
                )
        days.append(
            {
                "date": day.isoformat(),
                "cycle_phase": phase.value if phase else None,
                "meals": meals,
            }
        )

    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "days": days,
        "unpredictable_dates": [
            day.isoformat() for day in week_dates if day not in phases_by_date
        ],
        "items": await _sum_ingredients(db, servings_by_recipe),
    }


async def _get_logged_phases(
    db: AsyncSession, client_id: uuid.UUID, week_start: date, week_end: date
) -> dict[date, CyclePhase]:
    result = await db.execute(
        select(DailyLog.log_date, DailyLog.cycle_phase).where(
            DailyLog.client_id == client_id,
            DailyLog.log_date.between(week_start, week_end),
        )
    )
    return {log_date: cycle_phase for log_date, cycle_phase in result.all()}


async def _get_recipe_options(
    db: AsyncSession, client_id: uuid.UUID
) -> dict[tuple[CyclePhase, MealType], list[tuple[uuid.UUID, str]]]:
    result = await db.execute(
        select(
            NutritionPlanRecipe.cycle_phase,
            NutritionPlanRecipe.meal_type,
            Recipe.id,
            Recipe.name,
        )
        .join(NutritionPlan, NutritionPlanRecipe.nutrition_plan_id == NutritionPlan.id)
        .join(Recipe, NutritionPlanRecipe.recipe_id == Recipe.id)
        .where(
            NutritionPlan.client_id == client_id,
            NutritionPlan.is_active.is_(True),
        )
        .order_by(Recipe.name, Recipe.id)
    )
    options = defaultdict(list)
    for cycle_phase, meal_type, recipe_id, recipe_name in result.all():
        options[(cycle_phase, meal_type)].append((recipe_id, recipe_name))
    return options


async def _sum_ingredients(
    db: AsyncSession, servings_by_recipe: Counter[uuid.UUID]
) -> list[dict]:
    if not servings_by_recipe:
        return []
    servings = case(dict(servings_by_recipe), value=RecipeIngredient.recipe_id)
    result = await db.execute(
        select(
            Ingredient.name,
            RecipeIngredient.unit,
            func.sum(RecipeIngredient.quantity * servings),
        )
        .join(Ingredient, RecipeIngredient.ingredient_id == Ingredient.id)
        .where(RecipeIngredient.recipe_id.in_(servings_by_recipe.keys()))
        .group_by(Ingredient.name, RecipeIngredient.unit)
        .order_by(Ingredient.name, RecipeIngredient.unit)
    )
    return [
        {"ingredient": name, "quantity": str(quantity), "unit": unit}
        for name, unit, quantity in result.all()
    ]
