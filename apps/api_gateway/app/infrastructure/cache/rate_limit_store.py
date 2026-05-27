from fastapi import HTTPException, Request
import valkey.asyncio as valkey

from packages.config.settings import settings

_valkey_client: valkey.Valkey | None = None


def get_rate_limit_client() -> valkey.Valkey:
    global _valkey_client

    if _valkey_client is None:
        _valkey_client = valkey.from_url(
            settings.valkey_url,
            decode_responses=True,
        )

    return _valkey_client


async def rate_limit(request: Request, token_payload: dict) -> None:
    if not settings.gateway_rate_limit_enabled:
        return

    subject = token_payload.get("sub", "anonymous")
    key = f"gateway:rl:{subject}"
    client = get_rate_limit_client()

    try:
        count = await client.incr(key)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Gateway rate limiter unavailable",
        ) from exc

    if count == 1:
        await client.expire(key, settings.rate_limit_ttl_seconds)

    if count > settings.gateway_rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
