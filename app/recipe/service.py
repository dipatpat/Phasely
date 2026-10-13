import logging
import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import MealType
from app.recipe.models import DietaryTag, Ingredient, Recipe, RecipeIngredient
from app.recipe.schemas import IngredientCreate
from app.recipe.tasks import sync_recipe_to_postgres_full_text_search

logger = logging.getLogger(__name__)


class RecipeNotFoundError(Exception):
    pass


class RecipeInUseError(Exception):
    pass


async def _check_ingredients(
    db: AsyncSession, ingredients: list[IngredientCreate]
) -> list[RecipeIngredient]:
    recipe_ingredients: list[RecipeIngredient] = []
    for ingredient in ingredients:
        result = await db.execute(
            select(Ingredient).where(Ingredient.name == ingredient.name)
        )
        found_ingredient = result.scalar_one_or_none()
        if found_ingredient is None:
            found_ingredient = Ingredient(name=ingredient.name)
            db.add(found_ingredient)
        recipe_ingredients.append(
            RecipeIngredient(
                ingredient=found_ingredient,
                quantity=ingredient.quantity,
                unit=ingredient.unit,
            )
        )
    return recipe_ingredients


async def _check_dietary_tags(db: AsyncSession, names: list[str]) -> list[DietaryTag]:
    tags: list[DietaryTag] = []
    for name in set(names):
        result = await db.execute(select(DietaryTag).where(DietaryTag.name == name))
        tag = result.scalar_one_or_none()
        if tag is None:
            tag = DietaryTag(name=name)
            db.add(tag)
        tags.append(tag)
    return tags


async def create_recipe(
    db: AsyncSession,
    name: str,
    meal_type: MealType,
    protein: Decimal,
    carbs: Decimal,
    fat: Decimal,
    calories: int,
    serving_size: str,
    preparation_notes: str | None,
    ingredients: list[IngredientCreate],
    dietary_tag_names: list[str],
) -> Recipe:
    new_recipe = Recipe(
        name=name,
        meal_type=meal_type,
        protein=protein,
        carbs=carbs,
        fat=fat,
        calories=calories,
        serving_size=serving_size,
        preparation_notes=preparation_notes,
    )
    ingredients = await _check_ingredients(db, ingredients=ingredients)
    new_recipe.ingredients = ingredients
    new_recipe.dietary_tags = await _check_dietary_tags(db, names=dietary_tag_names)
    db.add(new_recipe)
    await db.commit()
    try:
        sync_recipe_to_postgres_full_text_search.delay(str(new_recipe.id))
    except Exception:
        logger.exception(
            "Failed to enqueue full-text search sync for recipe %s", new_recipe.id
        )
    return await get_recipe_by_id(db, new_recipe.id)


async def list_recipes(db: AsyncSession) -> list[Recipe]:
    result = await db.execute(
        select(Recipe).options(
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient),
            selectinload(Recipe.dietary_tags),
        )
    )
    return list(result.scalars().all())


async def get_recipe_by_id(db: AsyncSession, recipe_id: uuid.UUID) -> Recipe | None:
    result = await db.execute(
        select(Recipe)
        .options(
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient),
            selectinload(Recipe.dietary_tags),
        )
        .where(Recipe.id == recipe_id)
    )
    return result.scalar_one_or_none()


async def update_recipe(
    db: AsyncSession,
    recipe_id: uuid.UUID,
    name: str | None = None,
    meal_type: MealType | None = None,
    protein: Decimal | None = None,
    carbs: Decimal | None = None,
    fat: Decimal | None = None,
    calories: int | None = None,
    serving_size: str | None = None,
    preparation_notes: str | None = None,
    ingredients: list[IngredientCreate] | None = None,
    dietary_tag_names: list[str] | None = None,
) -> Recipe:
    recipe = await get_recipe_by_id(db, recipe_id)
    if recipe is None:
        raise RecipeNotFoundError("Recipe not found")
    if name is not None:
        recipe.name = name
    if meal_type is not None:
        recipe.meal_type = meal_type
    if protein is not None:
        recipe.protein = protein
    if carbs is not None:
        recipe.carbs = carbs
    if fat is not None:
        recipe.fat = fat
    if calories is not None:
        recipe.calories = calories
    if serving_size is not None:
        recipe.serving_size = serving_size
    if preparation_notes is not None:
        recipe.preparation_notes = preparation_notes
    if ingredients is not None:
        recipe.ingredients = await _check_ingredients(db, ingredients=ingredients)
    if dietary_tag_names is not None:
        recipe.dietary_tags = await _check_dietary_tags(db, names=dietary_tag_names)
    await db.commit()
    try:
        sync_recipe_to_postgres_full_text_search.delay(str(recipe.id))
    except Exception:
        logger.exception(
            "Failed to enqueue full-text search sync for recipe %s", recipe.id
        )

    return await get_recipe_by_id(db, recipe.id)


async def delete_recipe(db: AsyncSession, recipe_id: uuid.UUID) -> None:
    recipe = await get_recipe_by_id(db, recipe_id)
    if recipe is None:
        raise RecipeNotFoundError("Recipe not found")
    try:
        await db.delete(recipe)
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise RecipeInUseError("Recipe is used in a plan or log") from e
    return None


async def search_recipes(
    db: AsyncSession,
    query: str,
    meal_type: MealType | None = None,
    max_calories: int | None = None,
    min_protein: Decimal | None = None,
    dietary_tag: str | None = None,
    limit: int = 20,
) -> list[Recipe]:
    tsquery = func.websearch_to_tsquery("english", query)
    order_by_rank = func.ts_rank(Recipe.search_vector, tsquery)
    stmt = (
        select(Recipe)
        .options(
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient),
            selectinload(Recipe.dietary_tags),
        )
        .where(Recipe.search_vector.op("@@")(tsquery))
    )
    if meal_type is not None:
        stmt = stmt.where(Recipe.meal_type == meal_type)
    if max_calories is not None:
        stmt = stmt.where(Recipe.calories <= max_calories)
    if min_protein is not None:
        stmt = stmt.where(Recipe.protein >= min_protein)
    if dietary_tag is not None:
        stmt = stmt.where(Recipe.dietary_tags.any(DietaryTag.name == dietary_tag))
    stmt = stmt.order_by(order_by_rank.desc(), Recipe.name).limit(limit)

    result = await db.execute(stmt)
    return list(result.scalars().all())
