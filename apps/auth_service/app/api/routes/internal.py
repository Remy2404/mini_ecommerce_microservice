from typing import Any

from fastapi import APIRouter

from apps.auth_service.app.schemas.requests import WSO2PasswordLoginRequest

router = APIRouter()


@router.post("/internal/wso2/login", include_in_schema=False)
async def login_user(request: WSO2PasswordLoginRequest) -> dict[str, Any]:
    from apps.auth_service.app.api import routes as routes_module

    return await routes_module.request_wso2_password_token(
        username=request.username,
        password=request.password.get_secret_value(),
        scope=request.scope,
    )
