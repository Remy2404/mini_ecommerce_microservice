"""Async SQLAlchemy connection and ORM session helpers."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from packages.config.settings import settings
from packages.database.engine import get_async_engine
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for service-owned SQLAlchemy models."""


def get_sessionmaker(database_url: str) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        get_async_engine(database_url),
        expire_on_commit=False,
        autoflush=False,
    )


def get_service_sessionmaker(service_name: str) -> async_sessionmaker[AsyncSession]:
    database_urls = {
        "auth": settings.auth_database_url,
        "product": settings.products_database_url,
        "products": settings.products_database_url,
        "order": settings.orders_database_url,
        "orders": settings.orders_database_url,
        "payment": settings.payments_database_url,
        "payments": settings.payments_database_url,
    }
    try:
        database_url = database_urls[service_name]
    except KeyError as exc:
        raise ValueError(f"Unknown service database: {service_name}") from exc

    if not database_url:
        raise ValueError(f"Database URL is not configured for {service_name}")

    return get_sessionmaker(database_url)


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


auth_sessionmaker = get_sessionmaker(settings.auth_database_url) if settings.auth_database_url else None
products_sessionmaker = get_sessionmaker(settings.products_database_url)
orders_sessionmaker = get_sessionmaker(settings.orders_database_url)
payments_sessionmaker = get_sessionmaker(settings.payments_database_url)
