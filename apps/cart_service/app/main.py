from fastapi import FastAPI
from prometheus_client import make_asgi_app

from apps.cart_service.app.api.routes import router as cart_router
from apps.cart_service.app.infrastructure.config.settings import settings
from apps.cart_service.app.infrastructure.observability.http_metrics import (
    HTTPMetricsMiddleware,
)
from apps.cart_service.app.infrastructure.observability.logging import setup_logging
from apps.cart_service.app.infrastructure.observability.tracing import setup_tracing

app = FastAPI(
    title="Cart Service",
)

setup_logging(settings.cart_service_name)
setup_tracing(settings.cart_service_name, app)

app.mount("/metrics", make_asgi_app())
app.add_middleware(HTTPMetricsMiddleware, service_name=settings.cart_service_name)

app.include_router(cart_router)

