import httpx
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings

bearer_scheme = HTTPBearer()
_jwks_cache: dict = {}


async def get_jwks() -> dict:
    """Fetch and cache WSO2 public keys."""
    global _jwks_cache
    if not _jwks_cache:
        async with httpx.AsyncClient(verify=False) as client:
            r = await client.get(settings.WSO2_JWKS_URL)
            r.raise_for_status()
            _jwks_cache = r.json()   # ← store the full {"keys": [...]} dict
    return _jwks_cache


async def validate_token(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> dict:
    token = credentials.credentials
    try:
        jwks = await get_jwks()      # ← was missing await, this was the bug

        payload = jwt.decode(
            token,
            jwks,                    # ← now passes the actual dict, not a coroutine
            algorithms=["RS256"],
            audience=settings.WSO2_AUDIENCE,
            issuer=settings.WSO2_ISSUER,
        )
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")