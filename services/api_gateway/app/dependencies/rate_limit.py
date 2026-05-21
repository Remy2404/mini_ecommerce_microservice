import redis.asyncio as aioredis
from fastapi import HTTPException, Request
from app.config import settings

_redis = aioredis.from_url(settings.REDIS_URL)

async def rate_limit(request: Request, token_payload: dict):
    key = f"rl:{token_payload['sub']}"
    count = await _redis.incr(key)
    if count == 1:
        await _redis.expire(key, settings.RATE_LIMIT_WINDOW)
    if count > settings.RATE_LIMIT_REQUESTS:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")