import asyncio
import json
import uuid
from datetime import date, datetime, timedelta

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.celery import celery_app
from app.client.service import list_active_client_ids
from app.core.config import APP_TZ, settings
from app.report.service import generate_weekly_report_data

task_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
TaskSessionLocal = async_sessionmaker(task_engine, expire_on_commit=False)


def create_redis_client() -> aioredis.Redis:
    return aioredis.from_url(settings.REDIS_URL)


@celery_app.task(name="generate_weekly_report")
def generate_weekly_report(client_id: str, week_start: str) -> dict:
    return asyncio.run(_generate_weekly_report_async(client_id, week_start))


async def _generate_weekly_report_async(client_id: str, week_start: str) -> dict:
    client_uuid = uuid.UUID(client_id)
    week_start_date = date.fromisoformat(week_start)
    async with TaskSessionLocal() as db:
        report = await generate_weekly_report_data(db, client_uuid, week_start_date)

    redis = create_redis_client()
    try:
        cache_key = f"weekly_report:{client_id}:{week_start}"
        await redis.set(cache_key, json.dumps(report), ex=604800)
    finally:
        await redis.aclose()
    return report


def previous_week_start(today: date) -> date:
    return today - timedelta(days=today.weekday() + 7)


@celery_app.task(name="generate_all_weekly_reports")
def generate_all_weekly_reports() -> int:
    week_start = previous_week_start(datetime.now(APP_TZ).date())
    client_ids = asyncio.run(_list_active_client_ids())
    for client_id in client_ids:
        generate_weekly_report.delay(str(client_id), week_start.isoformat())
    return len(client_ids)


async def _list_active_client_ids() -> list[uuid.UUID]:
    async with TaskSessionLocal() as db:
        return await list_active_client_ids(db)
