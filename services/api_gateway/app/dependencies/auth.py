import httpx
from jose import jwt, JWTError
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status

from packages.config.settings import settings

bearer_scheme = HTTPBearer(auto_error=False)
_jwks_cache: dict = {}


async def get_jwks() -> dict:
    """Fetch and cache WSO2 public keys."""
    global _jwks_cache
    if not _jwks_cache:
        async with httpx.AsyncClient(
            timeout=settings.gateway_request_timeout_seconds,
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
        jwks = await get_jwks()

        payload = jwt.decode(
            token,
            jwks,
            algorithms=[settings.jwt_algorithm],
            audience=settings.wso2_audience,
            issuer=settings.wso2_issuer,
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc
