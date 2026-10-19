import json
import uuid
from datetime import date

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.client.dependencies import resolve_target_client_id
from app.core.database import get_db
from app.core.redis import get_redis
from app.report.schemas import WeeklyReportGenerate, WeeklyReportPublic
from app.report.tasks import generate_weekly_report
from app.user.models import User

router = APIRouter(prefix="/report", tags=["report"])


@router.post("/weekly", response_model=dict)
async def handle_generate_weekly_report(
    data: WeeklyReportGenerate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    client_id = await resolve_target_client_id(db, user, data.client_id)
    generate_weekly_report.delay(str(client_id), data.week_start.isoformat())
    return {"detail": "Report generation started"}


@router.get("/weekly", response_model=WeeklyReportPublic)
async def handle_get_weekly_report(
    week_start: date,
    client_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    target_client_id = await resolve_target_client_id(db, user, client_id)
    cache_key = f"weekly_report:{target_client_id}:{week_start.isoformat()}"
    cached = await redis.get(cache_key)
    if cached is None:
        raise HTTPException(status_code=404, detail="Report not available yet")
    return WeeklyReportPublic(**json.loads(cached))
