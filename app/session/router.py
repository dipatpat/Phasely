import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_client, require_trainer
from app.client.service import get_client_profile_by_id, get_client_profile_by_user_id
from app.core.database import get_db
from app.core.enums import UserRole
from app.session.schemas import (
    SessionCancel,
    SessionCreateByClient,
    SessionCreateByTrainer,
    SessionPublic,
)
from app.session.service import (
    InvalidTransitionError,
    SlotUnavailableError,
    book_session,
    cancel_session,
    complete_session,
    confirm_session,
    get_session_by_id,
    list_available_slots,
    list_session_for_user,
)
from app.trainer.schemas import TrainerAvailabilityPublic
from app.trainer.service import get_trainer_profile_by_user_id
from app.user.models import User

router = APIRouter(prefix="/session", tags=["session"])


@router.post(
    "/book-client", response_model=SessionPublic, status_code=status.HTTP_201_CREATED
)
async def handle_create_sesion_as_client(
    data: SessionCreateByClient,
    db: AsyncSession = Depends(get_db),
    client: User = Depends(require_client),
):
    client_profile = await get_client_profile_by_user_id(db, client.id)
    if client_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No client profile found"
        )
    try:
        new_session = await book_session(
            db=db,
            client_id=client_profile.id,
            trainer_id=client_profile.trainer_id,
            slot_date=data.scheduled_at.date(),
            slot_start=data.scheduled_at.time(),
            notes=data.notes,
        )
    except SlotUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slot not available",
        ) from e
    booked_session = await get_session_by_id(db, new_session.id)
    return booked_session


@router.post(
    "/book-trainer", response_model=SessionPublic, status_code=status.HTTP_201_CREATED
)
async def handle_create_sesion_as_trainer(
    data: SessionCreateByTrainer,
    db: AsyncSession = Depends(get_db),
    trainer: User = Depends(require_trainer),
):
    trainer_profile = await get_trainer_profile_by_user_id(db, trainer.id)
    if trainer_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No trainer profile found"
        )
    client_profile = await get_client_profile_by_id(
        db, data.client_id, trainer_profile.id
    )
    if client_profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Client not found")

    try:
        new_session = await book_session(
            db=db,
            client_id=data.client_id,
            trainer_id=trainer_profile.id,
            slot_date=data.scheduled_at.date(),
            slot_start=data.scheduled_at.time(),
            notes=data.notes,
        )
    except SlotUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slot not available",
        ) from e
    booked_session = await get_session_by_id(db, new_session.id)
    return booked_session


@router.patch("/confirm", response_model=SessionPublic, status_code=status.HTTP_200_OK)
async def handle_confirm_sesion(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    trainer: User = Depends(require_trainer),
):
    trainer_profile = await get_trainer_profile_by_user_id(db, trainer.id)
    if trainer_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No trainer profile found"
        )
    booked_session = await get_session_by_id(db, session_id)
    if booked_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    if booked_session.trainer_id != trainer_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your session"
        )
    try:
        booked_session = await confirm_session(db, booked_session)
    except InvalidTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Invalid state"
        ) from e

    return booked_session


@router.patch("/complete", response_model=SessionPublic, status_code=status.HTTP_200_OK)
async def handle_complete_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    trainer: User = Depends(require_trainer),
):
    trainer_profile = await get_trainer_profile_by_user_id(db, trainer.id)
    if trainer_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No trainer profile found"
        )
    booked_session = await get_session_by_id(db, session_id)
    if booked_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    if booked_session.trainer_id != trainer_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your session"
        )
    try:
        booked_session = await complete_session(db, booked_session)
    except InvalidTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Invalid state"
        ) from e

    return booked_session


@router.patch("/cancel", response_model=SessionPublic, status_code=status.HTTP_200_OK)
async def handle_cancel_session(
    session_id: uuid.UUID,
    data: SessionCancel,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    booked_session = await get_session_by_id(db, session_id)
    if booked_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    if user.role == UserRole.trainer:
        trainer_profile = await get_trainer_profile_by_user_id(db, user.id)
        if not trainer_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        if booked_session.trainer_id != trainer_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not your session"
            )
    if user.role == UserRole.client:
        client_profile = await get_client_profile_by_user_id(db, user.id)
        if not client_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        if booked_session.client_id != client_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not your session"
            )
    try:
        booked_session = await cancel_session(
            db, booked_session, reason=data.cancellation_reason
        )
    except InvalidTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Invalid state"
        ) from e

    return booked_session


@router.get(
    "/my_sessions", response_model=list[SessionPublic], status_code=status.HTTP_200_OK
)
async def handle_get_my_sessions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await list_session_for_user(db, user)

    return result


@router.get(
    "/available_slots",
    response_model=list[TrainerAvailabilityPublic],
    status_code=status.HTTP_200_OK,
)
async def handle_get_available_slots(
    date_target: date,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role == UserRole.trainer:
        trainer_profile = await get_trainer_profile_by_user_id(db, user.id)
        if not trainer_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        result = await list_available_slots(db, trainer_profile.id, date_target)

    if user.role == UserRole.client:
        client_profile = await get_client_profile_by_user_id(db, user.id)
        if not client_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        result = await list_available_slots(db, client_profile.trainer_id, date_target)

    return result
