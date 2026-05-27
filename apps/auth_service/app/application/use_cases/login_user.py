"""Login use case wrapper."""

from apps.auth_service.app.application.services import AuthService
from apps.auth_service.app.schemas.requests import LoginRequest
from apps.auth_service.app.schemas.responses import AuthTokenResponse


async def login_user(request: LoginRequest, service: AuthService) -> AuthTokenResponse:
    return await service.login_user(request)
