from fastapi import FastAPI
from prometheus_client import make_asgi_app

from ecommerce_config.settings import settings
from ecommerce_observability.http_metrics import HTTPMetricsMiddleware
from ecommerce_observability.logging import setup_logging
from ecommerce_observability.tracing import setup_tracing
from apps.product_service.app.api.routes import router as product_router

app = FastAPI(
    title="Product Service",
)

setup_logging(settings.product_service_name)
setup_tracing(settings.product_service_name, app)

app.mount("/metrics", make_asgi_app())
app.add_middleware(HTTPMetricsMiddleware, service_name=settings.product_service_name)

app.include_router(product_router)

