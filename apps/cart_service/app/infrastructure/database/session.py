from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from apps.cart_service.app.infrastructure.database.engine import get_async_engine


class Base(DeclarativeBase):
    """Shared declarative base for Cart Service-owned SQLAlchemy models."""


def get_sessionmaker(database_url: str) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        get_async_engine(database_url),
        expire_on_commit=False,
        autoflush=False,
    )


@asynccontextmanager
async def connect(database_url: str) -> AsyncIterator[AsyncConnection]:
    async with get_async_engine(database_url).connect() as connection:
        yield connection


@asynccontextmanager
async def transaction(database_url: str) -> AsyncIterator[AsyncConnection]:
    async with get_async_engine(database_url).begin() as connection:
        yield connection


@asynccontextmanager
async def session_scope(database_url: str) -> AsyncIterator[AsyncSession]:
    session_factory = get_sessionmaker(database_url)
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
