import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.client.service import get_client_profile_by_id, get_client_profile_by_user_id
from app.core.enums import UserRole
from app.trainer.service import get_trainer_profile_by_user_id
from app.user.models import User


async def resolve_target_client_id(
    db: AsyncSession, user: User, client_id: uuid.UUID | None
) -> uuid.UUID:
    if user.role == UserRole.trainer:
        trainer_profile = await get_trainer_profile_by_user_id(db, user.id)
        if trainer_profile is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No trainer profile found",
            )
        if client_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="client_id is required",
            )
        client_profile = await get_client_profile_by_id(
            db, client_id, trainer_profile.id
        )
        if client_profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
            )
        return client_profile.id

    if user.role == UserRole.client:
        client_profile = await get_client_profile_by_user_id(db, user.id)
        if client_profile is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No client profile found",
            )
        return client_profile.id

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Invalid user role"
    )
