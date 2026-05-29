"""Auth Service request and response DTOs."""

from apps.auth_service.app.schemas.requests import RegisterUserRequest
from apps.auth_service.app.schemas.responses import (
    RegisterUserResponse,
    Wso2UserName,
    Wso2UserDetailResponse,
    Wso2UserProfile,
    Wso2UsersListResponse,
)

__all__ = [
    "RegisterUserRequest",
    "RegisterUserResponse",
    "Wso2UserName",
    "Wso2UserDetailResponse",
    "Wso2UserProfile",
    "Wso2UsersListResponse",
]
