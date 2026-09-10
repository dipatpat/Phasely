import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_client, require_trainer
from app.client.schemas import (
    ClientProfileCreate,
    ClientProfilePublic,
    ClientProfileUpdate,
)
from app.client.service import (
    ClientProfileAlreadyExistsError,
    TrainerNotFoundError,
    create_client_profile,
    get_client_profile_by_id,
    get_client_profile_by_user_id,
    update_client_profile,
)
from app.core.database import get_db
from app.trainer.schemas import TrainerProfilePublic
from app.trainer.service import (
    get_trainer_profile_by_id,
    get_trainer_profile_by_user_id,
)
from app.user.models import User

router = APIRouter(prefix="/client", tags=["client"])


@router.post(
    "/create", response_model=ClientProfilePublic, status_code=status.HTTP_201_CREATED
)
async def handle_create_client_profile(
    data: ClientProfileCreate,
    user: User = Depends(require_client),
    db: AsyncSession = Depends(get_db),
):
    client_profile = await get_client_profile_by_user_id(db, user.id)
    if client_profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Client profile already exists",
        )
    try:
        new_client_profile = await create_client_profile(
            db,
            user.id,
            data.trainer_id,
            data.body_fat_percentage,
            data.fitness_goal,
            data.cycle_length_days,
            data.period_length_days,
            data.last_period_start,
        )
    except ClientProfileAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Client profile already exists",
        ) from e
    except TrainerNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trainer not found",
        ) from e

    return new_client_profile


@router.patch(
    "/update", response_model=ClientProfilePublic, status_code=status.HTTP_200_OK
)
async def handle_update_client_profile(
    data: ClientProfileUpdate,
    user: User = Depends(require_client),
    db: AsyncSession = Depends(get_db),
):
    client_profile = await get_client_profile_by_user_id(db, user.id)
    if not client_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client profile not found",
        )
    updated_client_profile = await update_client_profile(
        db,
        client_profile,
        data.body_fat_percentage,
        data.fitness_goal,
        data.cycle_length_days,
        data.period_length_days,
        data.last_period_start,
    )
    return updated_client_profile


@router.get("/", response_model=ClientProfilePublic, status_code=status.HTTP_200_OK)
async def handle_get_client_profile(
    user: User = Depends(require_client), db: AsyncSession = Depends(get_db)
):
    client_profile = await get_client_profile_by_user_id(db, user.id)
    if not client_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client profile not found",
        )
    return client_profile


@router.get("/my/trainer", response_model=TrainerProfilePublic)
async def handle_get_my_trainer(
    user: User = Depends(require_client), db: AsyncSession = Depends(get_db)
):
    client_profile = await get_client_profile_by_user_id(db, user.id)
    if not client_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )

    result = await get_trainer_profile_by_id(db, client_profile.trainer_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trainer not found"
        )
    return result


@router.get("/{client_id}", response_model=ClientProfilePublic)
async def handle_get_client_profile_by_id(
    client_id: uuid.UUID,
    user: User = Depends(require_trainer),
    db: AsyncSession = Depends(get_db),
):
    trainer_profile = await get_trainer_profile_by_user_id(db, user.id)
    if not trainer_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trainer profile not found"
        )
    client_profile = await get_client_profile_by_id(db, client_id, trainer_profile.id)
    if not client_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )
    return client_profile
