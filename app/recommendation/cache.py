import uuid
from datetime import date

import redis.asyncio as aioredis


async def invalidate_recommendations_cache(
    redis: aioredis.Redis, client_id: uuid.UUID
) -> None:
    cache_key = f"recommendations:{client_id}:{date.today()}"
    await redis.delete(cache_key)
