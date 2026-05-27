"""Database connection helpers."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from packages.database.engine import get_async_engine
from sqlalchemy.ext.asyncio import AsyncConnection


@asynccontextmanager
async def connect(database_url: str) -> AsyncIterator[AsyncConnection]:
    async with get_async_engine(database_url).connect() as connection:
        yield connection


@asynccontextmanager
async def transaction(database_url: str) -> AsyncIterator[AsyncConnection]:
    async with get_async_engine(database_url).begin() as connection:
        yield connection
