import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_trainer
from app.client.schemas import ClientProfilePublic
from app.client.service import list_clients_by_trainer_id
from app.core.database import get_db
from app.trainer.schemas import (
    TrainerAvailabilityCreate,
    TrainerAvailabilityPublic,
    TrainerAvailabilityUpdate,
    TrainerProfileCreate,
    TrainerProfilePublic,
    TrainerProfileUpdate,
)
from app.trainer.service import (
    TrainerProfileAlreadyExistsError,
    create_availability_slot,
    create_trainer_profile,
    delete_availability_slot,
    get_availability_slot,
    get_trainer_profile_by_id,
    get_trainer_profile_by_user_id,
    list_all_trainer_profiles,
    list_availability_slots,
    update_availability_slot,
    update_trainer_profile,
)
from app.user.models import User

router = APIRouter(prefix="/trainer", tags=["trainer"])


@router.post(
    "/create", response_model=TrainerProfilePublic, status_code=status.HTTP_201_CREATED
)
async def handle_create_trainer_profile(
    data: TrainerProfileCreate,
    user: User = Depends(require_trainer),
    db: AsyncSession = Depends(get_db),
):
    trainer_profile = await get_trainer_profile_by_user_id(db, user.id)
    if trainer_profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Trainer profile already exists",
        )
    try:
        new_trainer_profile = await create_trainer_profile(
            db, user.id, data.bio, data.specialization
        )
    except TrainerProfileAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Trainer profile already exists",
        ) from e
    return new_trainer_profile


@router.patch(
    "/update", response_model=TrainerProfilePublic, status_code=status.HTTP_200_OK
)
async def handle_update_trainer_profile(
    data: TrainerProfileUpdate,
    user: User = Depends(require_trainer),
    db: AsyncSession = Depends(get_db),
):
    trainer_profile = await get_trainer_profile_by_user_id(db, user.id)
    if not trainer_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trainer profile not found",
        )
    updated_trainer_profile = await update_trainer_profile(
        db, trainer_profile, data.bio, data.specialization
    )
    return updated_trainer_profile


@router.get("/", response_model=TrainerProfilePublic, status_code=status.HTTP_200_OK)
async def handle_get_trainer_profile(
    user: User = Depends(require_trainer), db: AsyncSession = Depends(get_db)
):
    trainer_profile = await get_trainer_profile_by_user_id(db, user.id)
    if not trainer_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trainer profile not found",
        )
    return trainer_profile


@router.post(
    "/availability",
    response_model=TrainerAvailabilityPublic,
    status_code=status.HTTP_201_CREATED,
)
async def handle_create_availability_slot(
    data: TrainerAvailabilityCreate,
    user: User = Depends(require_trainer),
    db: AsyncSession = Depends(get_db),
):
    trainer_profile = await get_trainer_profile_by_user_id(db, user.id)
    if not trainer_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trainer profile not found",
        )
    new_availability_slot = await create_availability_slot(
        db, trainer_profile.id, data.slot_date, data.slot_start, data.slot_end
    )
    return new_availability_slot


@router.patch(
    "/availability/{slot_id}",
    response_model=TrainerAvailabilityPublic,
    status_code=status.HTTP_200_OK,
)
async def handle_update_availability_slot(
    slot_id: uuid.UUID,
    data: TrainerAvailabilityUpdate,
    user: User = Depends(require_trainer),
    db: AsyncSession = Depends(get_db),
):
    trainer_profile = await get_trainer_profile_by_user_id(db, user.id)
    if not trainer_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trainer profile not found",
        )
    availability_slot = await get_availability_slot(db, slot_id, trainer_profile.id)
    if not availability_slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Availability slot not found",
        )
    updated_availability_slot = await update_availability_slot(
        db,
        availability_slot,
        data.slot_date,
        data.slot_start,
        data.slot_end,
        data.is_active,
    )
    return updated_availability_slot


@router.get(
    "/availability",
    response_model=list[TrainerAvailabilityPublic],
    status_code=status.HTTP_200_OK,
)
async def handle_get_availability_slots(
    user: User = Depends(require_trainer), db: AsyncSession = Depends(get_db)
):
    trainer_profile = await get_trainer_profile_by_user_id(db, user.id)
    if not trainer_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trainer profile not found",
        )
    availability_slots = await list_availability_slots(db, trainer_profile.id)
    return availability_slots


@router.get("/browse_trainers", response_model=list[TrainerProfilePublic])
async def handle_list_trainers(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    trainers = await list_all_trainer_profiles(db)
    return trainers


@router.get("/my_clients", response_model=list[ClientProfilePublic])
async def handle_get_clients(
    user: User = Depends(require_trainer), db: AsyncSession = Depends(get_db)
):
    trainer_profile = await get_trainer_profile_by_user_id(db, user.id)
    if not trainer_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trainer profile not found"
        )
    results = await list_clients_by_trainer_id(db, trainer_profile.id)
    return results


@router.get("/{trainer_id}", response_model=TrainerProfilePublic)
async def handle_get_trainer_profile_by_id(
    trainer_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    trainer_profile = await get_trainer_profile_by_id(db, trainer_id)
    if not trainer_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trainer not found"
        )
    return trainer_profile


@router.delete(
    "/availability/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def handle_delete_availability_slot(
    slot_id: uuid.UUID,
    user: User = Depends(require_trainer),
    db: AsyncSession = Depends(get_db),
):
    trainer_profile = await get_trainer_profile_by_user_id(db, user.id)
    if not trainer_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trainer profile not found",
        )
    availability_slot = await get_availability_slot(db, slot_id, trainer_profile.id)
    if not availability_slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Availability slot not found",
        )
    await delete_availability_slot(db, availability_slot)
