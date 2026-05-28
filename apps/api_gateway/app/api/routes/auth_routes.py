from typing import Any

from fastapi import APIRouter

from apps.api_gateway.app.schemas.requests import WSO2PasswordLoginRequest
from packages.security.wso2_login import request_wso2_password_token

router = APIRouter()


@router.post(
    "/internal/wso2/login",
    include_in_schema=False,
)
async def wso2_login(request: WSO2PasswordLoginRequest) -> dict[str, Any]:
    return await request_wso2_password_token(
        username=request.username,
        password=request.password.get_secret_value(),
        scope=request.scope,
    )
