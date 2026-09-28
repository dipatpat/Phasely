import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import MealType
from app.recipe.models import DietaryTag, Ingredient, Recipe, RecipeIngredient
from app.recipe.schemas import IngredientCreate


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
