"""Auth Service routes."""

from importlib import import_module

from fastapi import APIRouter

from apps.auth_service.app.application.services import get_auth_service as _get_auth_service
from apps.auth_service.app.infrastructure.security.wso2_login import (
    request_wso2_password_token as _request_wso2_password_token,
)
from apps.auth_service.app.infrastructure.security.wso2_scim import (
    WSO2SCIMError,
    filter_wso2_users as _filter_wso2_users,
    get_wso2_user_by_id as _get_wso2_user_by_id,
    search_wso2_users as _search_wso2_users,
)

get_auth_service = _get_auth_service
filter_wso2_users = _filter_wso2_users
search_wso2_users = _search_wso2_users
get_wso2_user_by_id = _get_wso2_user_by_id
request_wso2_password_token = _request_wso2_password_token

health_router = import_module(".health", __name__).router
internal_router = import_module(".internal", __name__).router
register_router = import_module(".register", __name__).router
scim_users_router = import_module(".scim_users", __name__).router

router = APIRouter()
router.include_router(health_router)
router.include_router(register_router)
router.include_router(scim_users_router)
router.include_router(internal_router)

__all__ = [
    "WSO2SCIMError",
    "filter_wso2_users",
    "get_auth_service",
    "get_wso2_user_by_id",
    "request_wso2_password_token",
    "router",
    "search_wso2_users",
]
