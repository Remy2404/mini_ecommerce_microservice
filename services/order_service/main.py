from contextlib import asynccontextmanager

from fastapi import FastAPI

from .router import router
from .models import Order
from .consumers import payment_result

from packages.messaging.broker import broker
from packages.database.primary import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):

    # STARTUP
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Orders table created")

    await broker.start()

    print("RabbitMQ broker connected")

    yield

    # SHUTDOWN
    await broker.close()

    print("RabbitMQ broker disconnected")


app = FastAPI(
    title="Order Service",
    lifespan=lifespan
)

app.include_router(router)