from fastapi import APIRouter

from apps.auth_service.app.infrastructure.config.settings import settings

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.auth_service_name}
