import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.plan.models import (
    NutritionPlan,
    NutritionPlanRecipe,
    TrainingPlan,
    TrainingPlanExercise,
)
from app.plan.schemas import (
    NutritionPlanRecipeCreate,
    TrainingPlanExerciseCreate,
)
from app.recipe.models import Recipe, RecipeIngredient


class PlanNotFoundError(Exception):
    pass


class ActivePlanExistsError(Exception):
    pass


class DuplicateAssignmentError(Exception):
    pass


class ItemNotFoundError(Exception):
    pass


async def create_nutrition_plan(
    db: AsyncSession,
    client_id: uuid.UUID,
    trainer_id: uuid.UUID,
    title: str,
    recipes: list[NutritionPlanRecipeCreate],
) -> NutritionPlan:
    assigned_recipes = []
    for recipe in recipes:
        assigned_recipes.append(
            NutritionPlanRecipe(
                recipe_id=recipe.recipe_id,
                meal_type=recipe.meal_type,
                cycle_phase=recipe.cycle_phase,
            )
        )
    new_plan = NutritionPlan(
        client_id=client_id,
        trainer_id=trainer_id,
        title=title,
        recipes=assigned_recipes,
    )
    try:
        db.add(new_plan)
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise ActivePlanExistsError("Active plan already exists") from e

    return await get_nutrition_plan_by_id(db, new_plan.id)


async def get_nutrition_plan_by_id(
    db: AsyncSession, plan_id: uuid.UUID
) -> NutritionPlan | None:
    result = await db.execute(
        select(NutritionPlan)
        .options(
            selectinload(NutritionPlan.recipes).selectinload(
                NutritionPlanRecipe.recipe
            ),
            selectinload(NutritionPlan.recipes)
            .selectinload(NutritionPlanRecipe.recipe)
            .selectinload(Recipe.ingredients)
            .selectinload(RecipeIngredient.ingredient),
            selectinload(NutritionPlan.recipes)
            .selectinload(NutritionPlanRecipe.recipe)
            .selectinload(Recipe.dietary_tags),
        )
        .where(NutritionPlan.id == plan_id)
    )
    return result.scalar_one_or_none()


async def update_nutrition_plan(
    db: AsyncSession,
    plan_id: uuid.UUID,
    is_active: bool | None = None,
    title: str | None = None,
    recipes: list[NutritionPlanRecipeCreate] | None = None,
) -> NutritionPlan:
    plan = await get_nutrition_plan_by_id(db, plan_id)
    if not plan:
        raise PlanNotFoundError("This plan doesn't exist")
    if is_active is not None:
        plan.is_active = is_active
    if title is not None:
        plan.title = title
    if recipes is not None:
        new_recipes = []
        for recipe in recipes:
            new_recipes.append(
                NutritionPlanRecipe(
                    recipe_id=recipe.recipe_id,
                    meal_type=recipe.meal_type,
                    cycle_phase=recipe.cycle_phase,
                )
            )
        plan.recipes.extend(new_recipes)
    try:
        await db.commit()
    except IntegrityError as e:
        raise DuplicateAssignmentError("The plan already exists") from e
    return await get_nutrition_plan_by_id(db, plan_id)


async def update_delete_recipe_from_plan(
    db: AsyncSession, plan_id: uuid.UUID, recipes: list[NutritionPlanRecipeCreate]
) -> NutritionPlan:
    plan = await get_nutrition_plan_by_id(db, plan_id)
    if not plan:
        raise PlanNotFoundError("This plan doesn't exist")
    for recipe in recipes:
        to_remove = None
        for item in plan.recipes:
            if (
                item.recipe_id == recipe.recipe_id
                and item.meal_type == recipe.meal_type
                and item.cycle_phase == recipe.cycle_phase
            ):
                to_remove = item
                break
        if to_remove is None:
            raise ItemNotFoundError("Recipe not found in the plan")
        plan.recipes.remove(to_remove)
    await db.commit()
    return plan


async def create_training_plan(
    db: AsyncSession,
    client_id: uuid.UUID,
    trainer_id: uuid.UUID,
    title: str,
    exercises: list[TrainingPlanExerciseCreate],
) -> TrainingPlan:
    assigned_exercises = []
    for exercise in exercises:
        assigned_exercises.append(
            TrainingPlanExercise(
                exercise_id=exercise.exercise_id,
                cycle_phase=exercise.cycle_phase,
                day_of_week=exercise.day_of_week,
                sets=exercise.sets,
                reps=exercise.reps,
                duration_seconds=exercise.duration_seconds,
                weight_kg=exercise.weight_kg,
                rest_seconds=exercise.rest_seconds,
                difficulty_level=exercise.difficulty_level,
            )
        )
    new_plan = TrainingPlan(
        client_id=client_id,
        trainer_id=trainer_id,
        title=title,
        exercises=assigned_exercises,
    )
    try:
        db.add(new_plan)
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise ActivePlanExistsError("Active plan already exists") from e

    return await get_training_plan_by_id(db, new_plan.id)


async def get_training_plan_by_id(
    db: AsyncSession, plan_id: uuid.UUID
) -> TrainingPlan | None:
    result = await db.execute(
        select(TrainingPlan)
        .options(
            selectinload(TrainingPlan.exercises).selectinload(
                TrainingPlanExercise.exercise
            )
        )
        .where(TrainingPlan.id == plan_id)
    )
    return result.scalar_one_or_none()


async def update_delete_exercise_from_plan(
    db: AsyncSession, plan_id: uuid.UUID, exercises: list[TrainingPlanExerciseCreate]
) -> TrainingPlan:
    plan = await get_training_plan_by_id(db, plan_id)
    if not plan:
        raise PlanNotFoundError("This plan doesn't exist")
    for exercise in exercises:
        to_remove = None
        for item in plan.exercises:
            if (
                item.exercise_id == exercise.exercise_id
                and item.day_of_week == exercise.day_of_week
                and item.cycle_phase == exercise.cycle_phase
            ):
                to_remove = item
                break
        if to_remove is None:
            raise ItemNotFoundError("Exercise not found in the plan")
        plan.exercises.remove(to_remove)
    await db.commit()
    return plan


async def update_exercise_plan(
    db: AsyncSession,
    plan_id: uuid.UUID,
    is_active: bool | None = None,
    title: str | None = None,
    exercises: list[TrainingPlanExerciseCreate] | None = None,
) -> TrainingPlan:
    plan = await get_training_plan_by_id(db, plan_id)
    if not plan:
        raise PlanNotFoundError("This plan doesn't exist")
    if is_active is not None:
        plan.is_active = is_active
    if title is not None:
        plan.title = title
    if exercises is not None:
        new_exercises = []
        for exercise in exercises:
            new_exercises.append(
                TrainingPlanExercise(
                    exercise_id=exercise.exercise_id,
                    cycle_phase=exercise.cycle_phase,
                    day_of_week=exercise.day_of_week,
                    sets=exercise.sets,
                    reps=exercise.reps,
                    duration_seconds=exercise.duration_seconds,
                    weight_kg=exercise.weight_kg,
                    rest_seconds=exercise.rest_seconds,
                    difficulty_level=exercise.difficulty_level,
                )
            )
        plan.exercises.extend(new_exercises)
    try:
        await db.commit()
    except IntegrityError as e:
        raise DuplicateAssignmentError("The plan already exists") from e
    return await get_training_plan_by_id(db, plan_id)
