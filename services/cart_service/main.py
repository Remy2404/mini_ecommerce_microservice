from fastapi import FastAPI
from prometheus_client import make_asgi_app

from packages.config.settings import settings
from packages.observability.http_metrics import HTTPMetricsMiddleware
from packages.observability.logging import setup_logging
from packages.observability.tracing import setup_tracing
from services.cart_service.service import (
    add_item_to_cart,
    delete_cart,
    delete_cart_item,
    find_cart,
)
from services.cart_service.router import router as cart_router

app = FastAPI(
    title="Cart Service",
)

setup_logging(settings.cart_service_name)
setup_tracing(settings.cart_service_name, app)

app.mount("/metrics", make_asgi_app())
app.add_middleware(HTTPMetricsMiddleware, service_name=settings.cart_service_name)

app.include_router(cart_router)
