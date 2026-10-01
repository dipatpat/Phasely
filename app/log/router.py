from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_client
from app.client.service import get_client_profile_by_user_id
from app.core.database import get_db
from app.log.schemas import DailyLogCreate, DailyLogPublic
from app.log.service import DailyLogAlreadyExistsError, create_daily_log
from app.user.models import User

router = APIRouter(prefix="/log", tags=["log"])


@router.post(
    "/daily/create", response_model=DailyLogPublic, status_code=status.HTTP_201_CREATED
)
async def handle_create_daily_log(
    data: DailyLogCreate,
    user: User = Depends(require_client),
    db: AsyncSession = Depends(get_db),
):
    client_profile = await get_client_profile_by_user_id(db, user.id)
    if client_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No client profile found"
        )
    try:
        new_log = await create_daily_log(
            db,
            client_profile.id,
            data.log_date,
            data.cycle_phase,
            data.hours_of_sleep,
            data.energy_level,
        )
    except DailyLogAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Already logged for this date"
        ) from e
    return new_log
