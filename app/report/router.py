import json
import uuid
from datetime import date

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.client.service import get_client_profile_by_id, get_client_profile_by_user_id
from app.core.database import get_db
from app.core.enums import UserRole
from app.core.redis import get_redis
from app.report.schemas import WeeklyReportGenerate, WeeklyReportPublic
from app.report.tasks import generate_weekly_report
from app.trainer.service import get_trainer_profile_by_user_id
from app.user.models import User

router = APIRouter(prefix="/report", tags=["report"])


@router.post("/weekly", response_model=dict)
async def handle_generate_weekly_report(
    data: WeeklyReportGenerate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role == UserRole.trainer:
        trainer_profile = await get_trainer_profile_by_user_id(db, user.id)
        if trainer_profile is None:
            raise HTTPException(status_code=403, detail="No trainer profile found")
        if data.client_id is None:
            raise HTTPException(status_code=422, detail="client_id is required")
        client_profile = await get_client_profile_by_id(
            db, data.client_id, trainer_profile.id
        )
        if client_profile is None:
            raise HTTPException(status_code=404, detail="Client not found")
        resolved_client_id = client_profile.id
    elif user.role == UserRole.client:
        client_profile = await get_client_profile_by_user_id(db, user.id)
        if client_profile is None:
            raise HTTPException(status_code=403, detail="No client profile found")
        resolved_client_id = client_profile.id
    else:
        raise HTTPException(status_code=403, detail="Invalid user role")

    generate_weekly_report.delay(str(resolved_client_id), data.week_start.isoformat())
    return {"detail": "Report generation started"}


@router.get("/weekly", response_model=WeeklyReportPublic)
async def handle_get_weekly_report(
    week_start: date,
    client_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    if user.role == UserRole.trainer:
        trainer_profile = await get_trainer_profile_by_user_id(db, user.id)
        if trainer_profile is None:
            raise HTTPException(status_code=403, detail="No trainer profile found")
        if client_id is None:
            raise HTTPException(status_code=422, detail="client_id is required")
        client_profile = await get_client_profile_by_id(
            db, client_id, trainer_profile.id
        )
        if client_profile is None:
            raise HTTPException(status_code=404, detail="Client not found")
        found_client_id = client_profile.id
    elif user.role == UserRole.client:
        client_profile = await get_client_profile_by_user_id(db, user.id)
        if client_profile is None:
            raise HTTPException(status_code=403, detail="No client profile found")
        found_client_id = client_profile.id
    else:
        raise HTTPException(status_code=403, detail="Invalid user role")

    cache_key = f"weekly_report:{found_client_id}:{week_start.isoformat()}"
    cached = await redis.get(cache_key)
    if cached is None:
        raise HTTPException(status_code=404, detail="Report not available yet")
    return WeeklyReportPublic(**json.loads(cached))
