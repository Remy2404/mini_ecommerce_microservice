"""Auth Service request and response DTOs."""

from apps.auth_service.app.schemas.common import ApiResponse
from apps.auth_service.app.schemas.requests import (
    RegisterUserRequest,
    WSO2PasswordLoginRequest,
)
from apps.auth_service.app.schemas.responses import (
    RegisterUserResponse,
    Wso2UserDetailResponse,
    Wso2UserProfile,
    Wso2UsersListResponse,
)

__all__ = [
    "ApiResponse",
    "RegisterUserRequest",
    "RegisterUserResponse",
    "Wso2UserDetailResponse",
    "Wso2UserProfile",
    "Wso2UsersListResponse",
    "WSO2PasswordLoginRequest",
]

