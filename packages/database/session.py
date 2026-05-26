"""Database connection helpers."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine


@lru_cache
def get_async_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(
        database_url,
        pool_pre_ping=True,
    )


@asynccontextmanager
async def connect(database_url: str) -> AsyncIterator[AsyncConnection]:
    async with get_async_engine(database_url).connect() as connection:
        yield connection


@asynccontextmanager
async def transaction(database_url: str) -> AsyncIterator[AsyncConnection]:
    async with get_async_engine(database_url).begin() as connection:
        yield connection
