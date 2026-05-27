"""Payment service entrypoint."""

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from apps.payment_service.app.api.routes import router as payment_router
from packages.config.settings import settings
from packages.observability.http_metrics import HTTPMetricsMiddleware
from packages.observability.logging import setup_logging
from packages.observability.tracing import setup_tracing

app = FastAPI(title="Payment Service")

setup_logging(settings.payment_service_name)
setup_tracing(settings.payment_service_name, app)

app.mount("/metrics", make_asgi_app())
app.add_middleware(HTTPMetricsMiddleware, service_name=settings.payment_service_name)
app.include_router(payment_router)
