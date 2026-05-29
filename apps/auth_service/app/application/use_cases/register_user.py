"""Registration use case wrapper."""

from apps.auth_service.app.application.services import AuthService
from apps.auth_service.app.schemas.requests import RegisterUserRequest
from apps.auth_service.app.schemas.responses import RegisterUserResponse


async def register_user(
    request: RegisterUserRequest,
    service: AuthService,
) -> RegisterUserResponse:
    return await service.register_user(request)
