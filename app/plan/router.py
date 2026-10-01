import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_client, require_trainer
from app.client.service import get_client_profile_by_id, get_client_profile_by_user_id
from app.core.database import get_db
from app.core.enums import UserRole
from app.plan.schemas import (
    NutritionPlanCreate,
    NutritionPlanPublic,
    NutritionPlanRecipeCreate,
    NutritionPlanUpdate,
    TrainingPlanCreate,
    TrainingPlanExerciseCreate,
    TrainingPlanPublic,
    TrainingPlanUpdate,
)
from app.plan.service import (
    ActivePlanExistsError,
    DuplicateAssignmentError,
    ItemNotFoundError,
    create_nutrition_plan,
    create_training_plan,
    get_active_nutrition_plan_by_client_id,
    get_active_training_plan_by_client_id,
    get_nutrition_plan_by_id,
    get_training_plan_by_id,
    update_delete_exercise_from_plan,
    update_delete_recipe_from_plan,
    update_exercise_plan,
    update_nutrition_plan,
)
from app.trainer.service import get_trainer_profile_by_user_id
from app.user.models import User

router = APIRouter(prefix="/plan", tags=["Plan"])


@router.post(
    "/nutrition/create",
    response_model=NutritionPlanPublic,
    status_code=status.HTTP_201_CREATED,
)
async def handle_create_nutrition_plan(
    data: NutritionPlanCreate,
    user: User = Depends(require_trainer),
    db: AsyncSession = Depends(get_db),
):
    trainer_profile = await get_trainer_profile_by_user_id(db, user.id)
    if trainer_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No trainer profile found"
        )
    client_profile = await get_client_profile_by_id(
        db, data.client_id, trainer_profile.id
    )
    if client_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )
    try:
        new_plan = await create_nutrition_plan(
            db, data.client_id, trainer_profile.id, data.title, data.recipes
        )
    except ActivePlanExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Client already has an active nutrition plan",
        ) from e
    except ItemNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more recipes not found",
        ) from e
    return new_plan


@router.patch(
    "/nutrition/update",
    response_model=NutritionPlanPublic,
    status_code=status.HTTP_200_OK,
)
async def handle_update_nutrition_plan(
    plan_id: uuid.UUID,
    data: NutritionPlanUpdate,
    user: User = Depends(require_trainer),
    db: AsyncSession = Depends(get_db),
):
    trainer_profile = await get_trainer_profile_by_user_id(db, user.id)
    if trainer_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No trainer profile found"
        )
    plan = await get_nutrition_plan_by_id(db, plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
        )
    if plan.trainer_id != trainer_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your plan"
        )
    try:
        updated_plan = await update_nutrition_plan(
            db, plan_id, data.is_active, data.title, data.recipes
        )
    except DuplicateAssignmentError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Recipe already assigned to this plan",
        ) from e
    except ItemNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more recipes not found",
        ) from e
    return updated_plan


@router.patch(
    "/nutrition/remove_recipe",
    response_model=NutritionPlanPublic,
    status_code=status.HTTP_200_OK,
)
async def handle_remove_recipe_from_plan(
    plan_id: uuid.UUID,
    recipes: list[NutritionPlanRecipeCreate],
    user: User = Depends(require_trainer),
    db: AsyncSession = Depends(get_db),
):
    trainer_profile = await get_trainer_profile_by_user_id(db, user.id)
    if trainer_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No trainer profile found"
        )
    plan = await get_nutrition_plan_by_id(db, plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
        )
    if plan.trainer_id != trainer_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your plan"
        )
    try:
        updated_plan = await update_delete_recipe_from_plan(db, plan_id, recipes)
    except ItemNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found on this plan",
        ) from e
    return updated_plan


@router.get(
    "/nutrition/mine",
    response_model=NutritionPlanPublic,
    status_code=status.HTTP_200_OK,
)
async def handle_get_my_nutrition_plan(
    user: User = Depends(require_client),
    db: AsyncSession = Depends(get_db),
):
    client_profile = await get_client_profile_by_user_id(db, user.id)
    if client_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No client profile found"
        )
    plan = await get_active_nutrition_plan_by_client_id(db, client_profile.id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active nutrition plan found",
        )
    return plan


@router.get(
    "/nutrition/{plan_id}",
    response_model=NutritionPlanPublic,
    status_code=status.HTTP_200_OK,
)
async def handle_get_nutrition_plan(
    plan_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role == UserRole.trainer:
        trainer_profile = await get_trainer_profile_by_user_id(db, user.id)
        if trainer_profile is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="No trainer profile found"
            )
        plan = await get_nutrition_plan_by_id(db, plan_id)
        if plan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
            )
        if plan.trainer_id != trainer_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not your plan"
            )
    elif user.role == UserRole.client:
        client_profile = await get_client_profile_by_user_id(db, user.id)
        if client_profile is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="No client profile found"
            )
        plan = await get_nutrition_plan_by_id(db, plan_id)
        if plan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
            )
        if plan.client_id != client_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not your plan"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid user role"
        )
    return plan


@router.post(
    "/training/create",
    response_model=TrainingPlanPublic,
    status_code=status.HTTP_201_CREATED,
)
async def handle_create_training_plan(
    data: TrainingPlanCreate,
    user: User = Depends(require_trainer),
    db: AsyncSession = Depends(get_db),
):
    trainer_profile = await get_trainer_profile_by_user_id(db, user.id)
    if trainer_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No trainer profile found"
        )
    client_profile = await get_client_profile_by_id(
        db, data.client_id, trainer_profile.id
    )
    if client_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )
    try:
        new_plan = await create_training_plan(
            db, data.client_id, trainer_profile.id, data.title, data.exercises
        )
    except ActivePlanExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Client already has an active training plan",
        ) from e
    except ItemNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more exercises not found",
        ) from e
    return new_plan


@router.patch(
    "/training/update",
    response_model=TrainingPlanPublic,
    status_code=status.HTTP_200_OK,
)
async def handle_update_training_plan(
    plan_id: uuid.UUID,
    data: TrainingPlanUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_trainer),
):
    trainer_profile = await get_trainer_profile_by_user_id(db, user.id)
    if trainer_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No trainer profile found"
        )
    plan = await get_training_plan_by_id(db, plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
        )
    if plan.trainer_id != trainer_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your plan"
        )
    try:
        updated_plan = await update_exercise_plan(
            db, plan_id, data.is_active, data.title, data.exercises
        )
    except DuplicateAssignmentError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Exercise already assigned to this plan",
        ) from e
    except ItemNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more exercises not found",
        ) from e
    return updated_plan


@router.patch(
    "/training/remove_exercise",
    response_model=TrainingPlanPublic,
    status_code=status.HTTP_200_OK,
)
async def handle_remove_exercise_from_plan(
    plan_id: uuid.UUID,
    exercises: list[TrainingPlanExerciseCreate],
    user: User = Depends(require_trainer),
    db: AsyncSession = Depends(get_db),
):
    trainer_profile = await get_trainer_profile_by_user_id(db, user.id)
    if trainer_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No trainer profile found"
        )
    plan = await get_training_plan_by_id(db, plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
        )
    if plan.trainer_id != trainer_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your plan"
        )
    try:
        updated_plan = await update_delete_exercise_from_plan(db, plan_id, exercises)
    except ItemNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found on this plan",
        ) from e
    return updated_plan


@router.get(
    "/training/mine", response_model=TrainingPlanPublic, status_code=status.HTTP_200_OK
)
async def handle_get_my_training_plan(
    user: User = Depends(require_client),
    db: AsyncSession = Depends(get_db),
):
    client_profile = await get_client_profile_by_user_id(db, user.id)
    if client_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No client profile found"
        )
    plan = await get_active_training_plan_by_client_id(db, client_profile.id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active training plan found",
        )
    return plan


@router.get(
    "/training/{plan_id}",
    response_model=TrainingPlanPublic,
    status_code=status.HTTP_200_OK,
)
async def handle_get_training_plan(
    plan_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role == UserRole.trainer:
        trainer_profile = await get_trainer_profile_by_user_id(db, user.id)
        if trainer_profile is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="No trainer profile found"
            )
        plan = await get_training_plan_by_id(db, plan_id)
        if plan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
            )
        if plan.trainer_id != trainer_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not your plan"
            )
    elif user.role == UserRole.client:
        client_profile = await get_client_profile_by_user_id(db, user.id)
        if client_profile is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="No client profile found"
            )
        plan = await get_training_plan_by_id(db, plan_id)
        if plan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
            )
        if plan.client_id != client_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not your plan"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid user role"
        )
    return plan
