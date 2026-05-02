import redis.asyncio as aioredis
from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"database": "ok"}


@app.get("/health/redis")
async def health_redis():
    client = aioredis.from_url(settings.REDIS_URL)
    await client.ping()
    await client.aclose()
    return {"redis": "ok"}
