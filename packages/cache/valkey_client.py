from collections.abc import Callable
from functools import lru_cache
from typing import TypeVar

import valkey
import valkey.asyncio as async_valkey

from packages.config.settings import settings

T = TypeVar("T")


@lru_cache
def get_valkey_client() -> valkey.Valkey:
    return valkey.from_url(
        settings.valkey_url,
        decode_responses=True,
    )


@lru_cache
def get_async_valkey_client() -> async_valkey.Valkey:
    return async_valkey.from_url(
        settings.valkey_url,
        decode_responses=True,
    )


def cache_get(key: str) -> str | None:
    return get_valkey_client().get(key)


def cache_set(key: str, value: str, *, ttl_seconds: int | None = None) -> None:
    get_valkey_client().set(key, value, ex=ttl_seconds)


def cache_delete(key: str) -> None:
    get_valkey_client().delete(key)


async def get_or_set_json(
    key: str,
    loader: Callable[[], T],
    *,
    ttl_seconds: int,
    dumps: Callable[[T], str],
    loads: Callable[[str], T],
) -> T:
    client = get_async_valkey_client()
    cached = await client.get(key)
    if cached is not None:
        return loads(str(cached))

    value = loader()
    await client.set(key, dumps(value), ex=ttl_seconds)
    return value


async def acquire_lock(key: str, *, ttl_seconds: int) -> bool:
    return bool(await get_async_valkey_client().set(key, "1", nx=True, ex=ttl_seconds))


async def release_lock(key: str) -> None:
    await get_async_valkey_client().delete(key)
