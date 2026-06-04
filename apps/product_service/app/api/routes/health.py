"""Health route."""

from fastapi import APIRouter

from apps.product_service.app.infrastructure.config.settings import settings
from apps.product_service.app.infrastructure.observability.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/health")
async def health() -> dict[str, str]:
    logger.info("Health check requested")

    return {
        "status": "ok",
        "service": settings.product_service_name,
    }
