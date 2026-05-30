"""Auth Service orchestration."""

from apps.auth_service.app.schemas.requests import RegisterUserRequest
from apps.auth_service.app.schemas.responses import RegisterUserResponse
from packages.security.wso2_scim import register_wso2_user


class AuthService:
    async def register_user(
        self,
        request: RegisterUserRequest,
        *,
        request_id: str | None = None,
    ) -> RegisterUserResponse:
        user = await register_wso2_user(
            username=request.username,
            email=str(request.email),
            password=request.password.get_secret_value(),
            given_name=request.first_name,
            family_name=request.last_name,
            request_id=request_id,
        )
        return RegisterUserResponse(**user)


def get_auth_service() -> AuthService:
    return AuthService()
