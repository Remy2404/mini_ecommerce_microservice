"""WSO2 token validation helpers."""

from __future__ import annotations

import httpx
from jose import JWTError, jwt

from packages.config.settings import settings

_jwks_cache: dict = {}


class TokenValidationError(ValueError):
	"""Raised when an access token is invalid."""


class AuthProviderUnavailableError(RuntimeError):
	"""Raised when WSO2 endpoints are unavailable."""


def _is_jwt_token(token: str) -> bool:
	return token.count(".") == 2


async def get_jwks() -> dict:
	"""Fetch and cache WSO2 JWKS keys."""
	global _jwks_cache
	if _jwks_cache:
		return _jwks_cache

	async with httpx.AsyncClient(
		timeout=settings.wso2_request_timeout_seconds,
		verify=settings.wso2_verify_ssl,
	) as client:
		try:
			response = await client.get(settings.wso2_jwks_url)
			response.raise_for_status()
		except httpx.HTTPError as exc:
			raise AuthProviderUnavailableError("Unable to fetch WSO2 JWKS") from exc

	_jwks_cache = response.json()
	return _jwks_cache


async def introspect_access_token(token: str) -> dict:
	"""Validate an opaque WSO2 access token via introspection."""
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
		raise AuthProviderUnavailableError("Unable to introspect access token") from exc

	if response.status_code >= 500:
		raise AuthProviderUnavailableError("WSO2 introspection endpoint is unavailable")

	if response.status_code >= 400:
		raise TokenValidationError("Invalid token")

	try:
		payload = response.json()
	except ValueError as exc:
		raise AuthProviderUnavailableError("Invalid introspection response") from exc

	if not isinstance(payload, dict) or payload.get("active") is not True:
		raise TokenValidationError("Invalid token")

	return payload


async def validate_jwt_token(token: str) -> dict:
	jwks = await get_jwks()
	try:
		return jwt.decode(
			token,
			jwks,
			algorithms=[settings.jwt_algorithm],
			audience=settings.wso2_audience,
			issuer=settings.wso2_issuer,
		)
	except JWTError as exc:
		raise TokenValidationError("Invalid token") from exc


async def validate_wso2_access_token(token: str) -> dict:
	"""Validate a WSO2 access token (JWT or opaque)."""
	if _is_jwt_token(token):
		return await validate_jwt_token(token)

	return await introspect_access_token(token)


__all__ = [
	"AuthProviderUnavailableError",
	"TokenValidationError",
	"get_jwks",
	"introspect_access_token",
	"validate_jwt_token",
	"validate_wso2_access_token",
]
