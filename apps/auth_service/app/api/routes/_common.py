from fastapi import HTTPException, Request, status

from apps.auth_service.app.infrastructure.observability.logging import get_logger

logger = get_logger(__name__)


def get_request_id(request: Request) -> str | None:
    return request.headers.get("x-request-id")


def raise_http_wso2_error(exc: Exception, *, request_id: str | None) -> None:
    from apps.auth_service.app.infrastructure.security.wso2_scim import WSO2SCIMError

    if not isinstance(exc, WSO2SCIMError):
        raise exc

    logger.error(
        "WSO2 request failed",
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


def forbidden_if_missing_user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authenticated user",
        )
    return user_id
