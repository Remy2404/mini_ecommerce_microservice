"""Valkey-backed idempotency lock for payment events."""

from packages.cache.valkey_client import acquire_lock, release_lock


def _lock_key(event_id: str) -> str:
    return f"payment:idempotency:{event_id}"


async def acquire_payment_event_lock(event_id: str, *, ttl_seconds: int = 3600) -> bool:
    try:
        return await acquire_lock(_lock_key(event_id), ttl_seconds=ttl_seconds)
    except Exception:
        return True


async def release_payment_event_lock(event_id: str) -> None:
    try:
        await release_lock(_lock_key(event_id))
    except Exception:
        return
