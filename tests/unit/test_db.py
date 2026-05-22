import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "postgresql+asyncpg://ecommerce:ecommerce@127.0.0.1:15432/ecommerce"


async def main() -> None:
    engine = create_async_engine(DATABASE_URL, echo=True)

    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT 1"))
        print(result.scalar_one())

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
