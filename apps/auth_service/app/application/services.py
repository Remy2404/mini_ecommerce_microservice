"""Auth Service orchestration."""

from apps.auth_service.app.schemas.requests import RegisterUserRequest
from apps.auth_service.app.schemas.responses import RegisterUserResponse
from apps.auth_service.app.domain.entities import RegisteredUser
from apps.auth_service.app.infrastructure.security.wso2_scim import (
    register_wso2_user,
)


class AuthService:
    async def register_user(
        self,
        request: RegisterUserRequest,
        *,
        request_id: str | None = None,
    ) -> RegisterUserResponse:
        registration_result = await register_wso2_user(
            username=request.username,
            email=str(request.email),
            password=request.password.get_secret_value(),
            given_name=request.first_name,
            family_name=request.last_name,
            request_id=request_id,
        )
        user = RegisteredUser.from_registration_result(
            registration_result,
            requested_username=request.username,
            requested_email=str(request.email),
            first_name=request.first_name,
            last_name=request.last_name,
        )
        return RegisterUserResponse(**user.to_response_payload())


def get_auth_service() -> AuthService:
    return AuthService()

