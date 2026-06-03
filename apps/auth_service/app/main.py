"""Auth Service entrypoint."""

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from apps.auth_service.app.api.routes import router as auth_router
from ecommerce_config.settings import settings
from ecommerce_observability.http_metrics import HTTPMetricsMiddleware
from ecommerce_observability.logging import setup_logging
from ecommerce_observability.tracing import setup_tracing

app = FastAPI(title="Auth Service")

setup_logging(settings.auth_service_name)
setup_tracing(settings.auth_service_name, app)

app.mount("/metrics", make_asgi_app())
app.add_middleware(HTTPMetricsMiddleware, service_name=settings.auth_service_name)
app.include_router(auth_router)

