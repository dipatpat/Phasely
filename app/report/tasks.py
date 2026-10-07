import asyncio
import json
import uuid
from datetime import date

from app.celery import celery_app
from app.core.database import AsyncSessionLocal
from app.core.redis import get_redis
from app.report.service import generate_weekly_report_data


@celery_app.task(name="generate_weekly_report")
def generate_weekly_report(client_id: str, week_start: str) -> dict:
    return asyncio.run(_generate_weekly_report_async(client_id, week_start))


async def _generate_weekly_report_async(client_id: str, week_start: str) -> dict:
    client_uuid = uuid.UUID(client_id)
    week_start_date = date.fromisoformat(week_start)
    async with AsyncSessionLocal() as db:
        report = await generate_weekly_report_data(db, client_uuid, week_start_date)

    redis = await get_redis()
    cache_key = f"weekly_report:{client_id}:{week_start}"
    await redis.set(cache_key, json.dumps(report), ex=604800)
    return report
