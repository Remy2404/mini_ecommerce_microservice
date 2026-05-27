import httpx
from jose import jwt, JWTError
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status

from packages.config.settings import settings
from packages.errors.exceptions import UnauthorizedError
from packages.security.jwt import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)
_jwks_cache: dict = {}


def _invalid_token() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
    )


def _is_jwt_token(token: str) -> bool:
    return token.count(".") == 2


async def get_jwks() -> dict:
    """Fetch and cache WSO2 public keys."""
    global _jwks_cache
    if not _jwks_cache:
        async with httpx.AsyncClient(
            timeout=settings.wso2_request_timeout_seconds,
            verify=settings.wso2_verify_ssl,
        ) as client:
            try:
                response = await client.get(settings.wso2_jwks_url)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication service unavailable",
                ) from exc

            _jwks_cache = response.json()
    return _jwks_cache


async def introspect_access_token(token: str) -> dict:
    """Validate an opaque WSO2 access token through the introspection endpoint."""
    try:
        async with httpx.AsyncClient(
            timeout=settings.wso2_request_timeout_seconds,
            verify=settings.wso2_verify_ssl,
        ) as client:
            response = await client.post(
                settings.wso2_introspection_url,
                data={
                    "token": token,
                    "token_type_hint": "access_token",
                },
                auth=(settings.wso2_client_id, settings.wso2_client_secret),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        ) from exc

    if response.status_code >= 500:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )

    if response.status_code >= 400:
        raise _invalid_token()

    try:
        payload = response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        ) from exc

    if not isinstance(payload, dict) or payload.get("active") is not True:
        raise _invalid_token()

    return payload


async def validate_jwt_token(token: str) -> dict:
    jwks = await get_jwks()
    return jwt.decode(
        token,
        jwks,
        algorithms=[settings.jwt_algorithm],
        audience=settings.wso2_audience,
        issuer=settings.wso2_issuer,
    )


async def validate_token(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> dict:
    if not settings.gateway_auth_enabled:
        return {"sub": "local-demo"}

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    token = credentials.credentials
    try:
        if _is_jwt_token(token):
            if settings.jwt_secret_key.get_secret_value():
                try:
                    return decode_access_token(token)
                except UnauthorizedError:
                    return await validate_jwt_token(token)

            return await validate_jwt_token(token)

        return await introspect_access_token(token)
    except JWTError as exc:
        raise _invalid_token() from exc
