from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


@lru_cache
def get_async_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(
        database_url,
        pool_pre_ping=True,
    )
