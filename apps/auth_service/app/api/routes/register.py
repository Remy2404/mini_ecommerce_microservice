from fastapi import APIRouter, Depends, HTTPException, Request, status

from apps.auth_service.app.api import routes as routes_module
from apps.auth_service.app.api.routes._common import get_request_id
from apps.auth_service.app.application.services import AuthService
from apps.auth_service.app.infrastructure.observability.logging import get_logger
from apps.auth_service.app.infrastructure.security.wso2_scim import WSO2SCIMError
from apps.auth_service.app.schemas.common import ApiResponse
from apps.auth_service.app.schemas.requests import RegisterUserRequest
from apps.auth_service.app.schemas.responses import RegisterUserResponse

router = APIRouter(prefix="/auth")
logger = get_logger(__name__)


@router.post(
    "/register",
    response_model=ApiResponse[RegisterUserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register user with WSO2",
    description="Creates a new user in WSO2 Identity Server using SCIM2.",
)
async def register_user(
    request: Request,
    payload: RegisterUserRequest,
    service: AuthService = Depends(routes_module.get_auth_service),
) -> ApiResponse[RegisterUserResponse]:
    request_id = get_request_id(request)
    try:
        user = await service.register_user(payload, request_id=request_id)
    except WSO2SCIMError as exc:
        logger.error(
            "WSO2 user registration failed",
            request_id=request_id,
            target_url=exc.target_url,
            status_code=exc.status_code,
            error_type=exc.error_type,
            wso2_error_code=exc.wso2_error_code,
        )
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc

    return ApiResponse(
        success=True,
        message="User registered successfully",
        data=user,
    )
