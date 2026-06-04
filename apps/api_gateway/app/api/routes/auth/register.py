from fastapi import APIRouter, Request, status

from apps.api_gateway.app.infrastructure.http.proxy_client import forward_request
from apps.api_gateway.app.schemas.requests import GatewayRegisterUserRequest, swagger_request_body
from apps.api_gateway.app.schemas.responses import DetailErrorResponse, GatewayRegisterUserResponse

router = APIRouter(prefix="/auth")


@router.post(
    "/register",
    tags=["WSO2 Gateway"],
    status_code=status.HTTP_201_CREATED,
    response_model=GatewayRegisterUserResponse,
    summary="Register user in WSO2 Identity Server",
    description=(
        "Creates a WSO2 Identity Server user through SCIM2. WSO2 client "
        "credentials stay behind the backend."
    ),
    responses={
        503: {
            "model": DetailErrorResponse,
            "description": "WSO2 is unavailable or registration is not configured.",
        },
    },
    openapi_extra=swagger_request_body(GatewayRegisterUserRequest),
)
async def register_user(
    request: Request,
):
    return await forward_request("auth", "register", request)
