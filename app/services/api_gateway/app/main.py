from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from packages.config.settings import settings
from packages.observability.http_metrics import HTTPMetricsMiddleware
from packages.observability.logging import setup_logging
from app.services.api_gateway.app.middleware.error_handler import ErrorHandlerMiddleware
from app.services.api_gateway.app.middleware.logging import LoggingMiddleware
from app.services.api_gateway.app.routers.auth_routes import router as auth_routes_router
from app.services.api_gateway.app.routers.gateway_routes import (
    router as gateway_routes_router,
)
from app.services.api_gateway.app.routers.proxy import router

setup_logging(settings.api_gateway_service_name)

app = FastAPI(
    title="API Gateway",
    version="1.0",
    redirect_slashes=False,
)

app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(
    HTTPMetricsMiddleware,
    service_name=settings.api_gateway_service_name,
)
app.add_middleware(LoggingMiddleware)

app.include_router(auth_routes_router)
app.include_router(gateway_routes_router, prefix="/api/v1")
app.include_router(router, prefix="/api/v1")


@app.get("/health", tags=["Gateway Health"])
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.api_gateway_service_name,
    }


@app.get("/metrics", include_in_schema=False)
@app.get("/metrics/", include_in_schema=False)
async def metrics() -> Response:
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
