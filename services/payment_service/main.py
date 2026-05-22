"""Payment service entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from packages.database.primary import engine, Base

# IMPORTANT: import model so SQLAlchemy registers table
from .models import Payment

from .router import router


@asynccontextmanager
async def lifespan(app: FastAPI):

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield


app = FastAPI(
    title="Payment Service",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router)


@app.get("/health")
async def health():
    return {
        "success": True,
        "message": "Payment service healthy"
    }