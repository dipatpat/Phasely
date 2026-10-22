import uuid
from datetime import datetime

import redis.asyncio as aioredis

from app.core.config import APP_TZ


async def invalidate_recommendations_cache(
    redis: aioredis.Redis, client_id: uuid.UUID
) -> None:
    today = datetime.now(APP_TZ).date()
    cache_key = f"recommendations:{client_id}:{today}"
    await redis.delete(cache_key)
