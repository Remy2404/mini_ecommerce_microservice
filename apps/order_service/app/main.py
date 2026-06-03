"""Order service entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from ecommerce_config.settings import settings
from ecommerce_messaging.broker import broker
from ecommerce_observability.logging import get_logger, setup_logging
from ecommerce_observability.http_metrics import HTTPMetricsMiddleware
from ecommerce_observability.tracing import setup_tracing
from apps.order_service.app.api.routes import router as order_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await broker.connect()
    logger.info("RabbitMQ broker connected")
    yield
    await broker.stop()
    logger.info("RabbitMQ broker disconnected")


app = FastAPI(
    title="Order Service",
    lifespan=lifespan,
)

setup_logging(settings.order_service_name)
setup_tracing(settings.order_service_name, app)

app.mount("/metrics", make_asgi_app())
app.add_middleware(HTTPMetricsMiddleware, service_name=settings.order_service_name)

logger = get_logger(__name__)

app.include_router(order_router)

