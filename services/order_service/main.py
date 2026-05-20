import code
from turtle import st

from fastapi import FastAPI

from packages.config.settings import settings
from packages.observability.logging import get_logger, setup_logging
from packages.observability.tracing import setup_tracing

app = FastAPI(
    title="Order Service",
)

setup_logging(settings.order_service_name)
setup_tracing(settings.order_service_name, app)

logger = get_logger(__name__)


@app.get("/health")
def health():
    logger.info("Health check requested")

    return {
        # status code 200 is implied by FastAPI for successful responses, so we don't need to include it in the response body
        "status": "ok", 
        "status_code": 200,
        "service": settings.order_service_name,
    }
