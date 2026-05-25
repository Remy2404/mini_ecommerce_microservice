from fastapi import FastAPI
from prometheus_client import make_asgi_app

from packages.config.settings import settings
from packages.observability.http_metrics import HTTPMetricsMiddleware
from packages.observability.logging import setup_logging
from packages.observability.tracing import setup_tracing
from services.product_service.router import router as product_router

app = FastAPI(
    title="Product Service",
)

setup_logging(settings.product_service_name)
setup_tracing(settings.product_service_name, app)

app.mount("/metrics", make_asgi_app())
app.add_middleware(HTTPMetricsMiddleware, service_name=settings.product_service_name)

app.include_router(product_router)
