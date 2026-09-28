import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_trainer
from app.core.database import get_db
from app.recipe.schemas import RecipeCreate, RecipePublic, RecipeUpdate
from app.recipe.service import (
    RecipeInUseError,
    RecipeNotFoundError,
    create_recipe,
    delete_recipe,
    get_recipe_by_id,
    list_recipes,
    update_recipe,
)
from app.user.models import User

router = APIRouter(prefix="/recipe", tags=["recipe"])


@router.post(
    "/create", response_model=RecipePublic, status_code=status.HTTP_201_CREATED
)
async def handle_create_recipe(
    data: RecipeCreate,
    user: User = Depends(require_trainer),
    db: AsyncSession = Depends(get_db),
):
    new_recipe = await create_recipe(
        db,
        data.name,
        data.meal_type,
        data.protein,
        data.carbs,
        data.fat,
        data.calories,
        data.serving_size,
        data.preparation_notes,
        data.ingredients,
        data.dietary_tag_names,
    )
    return new_recipe


@router.patch("/update", response_model=RecipePublic, status_code=status.HTTP_200_OK)
async def handle_update_recipe(
    recipe_id: uuid.UUID,
    data: RecipeUpdate,
    user: User = Depends(require_trainer),
    db: AsyncSession = Depends(get_db),
):
    try:
        new_recipe = await update_recipe(
            db,
            recipe_id,
            data.name,
            data.meal_type,
            data.protein,
            data.carbs,
            data.fat,
            data.calories,
            data.serving_size,
            data.preparation_notes,
            data.ingredients,
            data.dietary_tag_names,
        )
    except RecipeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
        ) from e
    return new_recipe


@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def handle_delete_recipe(
    recipe_id: uuid.UUID,
    user: User = Depends(require_trainer),
    db: AsyncSession = Depends(get_db),
):
    try:
        await delete_recipe(db, recipe_id)
    except RecipeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
        ) from e
    except RecipeInUseError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Recipe is used in a plan"
        ) from e
    return None


@router.get("/", response_model=list[RecipePublic], status_code=status.HTTP_200_OK)
async def handle_get_recipes(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    recipes = await list_recipes(db)
    return recipes


@router.get("/by_id", response_model=RecipePublic, status_code=status.HTTP_200_OK)
async def handle_get_recipe_by_id(
    recipe_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    recipe = await get_recipe_by_id(db, recipe_id)
    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
        )
    return recipe
