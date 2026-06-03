"""Product Service security helpers."""

from apps.product_service.app.infrastructure.security.headers import (
    AUTHENTICATED_USER_ID_HEADER,
)
from apps.product_service.app.infrastructure.security.jwt_validator import (
    AuthProviderUnavailableError,
    TokenValidationError,
    get_jwks,
    introspect_access_token,
    validate_jwt_token,
    validate_wso2_access_token,
)
from apps.product_service.app.infrastructure.security.permissions import (
    has_role,
    has_scope,
    require_owner_or_role,
    require_role,
    require_scope,
)

__all__ = [
    "AUTHENTICATED_USER_ID_HEADER",
    "AuthProviderUnavailableError",
    "TokenValidationError",
    "get_jwks",
    "has_role",
    "has_scope",
    "introspect_access_token",
    "require_owner_or_role",
    "require_role",
    "require_scope",
    "validate_jwt_token",
    "validate_wso2_access_token",
]

