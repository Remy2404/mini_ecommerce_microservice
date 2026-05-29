"""WSO2 SCIM2 user management helpers."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

import httpx

from packages.config.settings import settings
from packages.observability.logging import get_logger


class WSO2SCIMError(RuntimeError):
    """Raised when WSO2 SCIM cannot complete a safe user operation."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = HTTPStatus.SERVICE_UNAVAILABLE,
        error_type: str = "scim_error",
        target_url: str | None = None,
        wso2_error_code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = int(status_code)
        self.error_type = error_type
        self.target_url = target_url
        self.wso2_error_code = wso2_error_code


logger = get_logger(__name__)


def _scim_url(path: str) -> str:
    return f"{settings.wso2_base_url.rstrip('/')}/scim2/{path.lstrip('/')}"


def _log_wso2_event(
    level: str,
    message: str,
    *,
    request_id: str | None,
    target_url: str,
    status_code: int | None = None,
    error_type: str | None = None,
    wso2_error_code: str | None = None,
) -> None:
    log_method = getattr(logger, level, logger.info)
    log_method(
        message,
        request_id=request_id,
        target_url=target_url,
        status_code=status_code,
        error_type=error_type,
        wso2_error_code=wso2_error_code,
    )


def _safe_wso2_error_code(response: httpx.Response) -> str | None:
    try:
        payload = response.json()
    except ValueError:
        return None

    if not isinstance(payload, dict):
        return None

    for key in ("scimType", "error", "code", "status"):
        value = payload.get(key)
        if isinstance(value, str | int):
            return str(value)

    return None


def _service_basic_auth() -> tuple[str, str]:
    return settings.wso2_client_id, settings.wso2_client_secret


# ---------------------------------------------------------------------------
# Error mapping: WSO2 upstream to downstream HTTP status
# ---------------------------------------------------------------------------


def _raise_scim_error(
    *,
    operation: str,
    response: httpx.Response,
    request_id: str | None,
    target_url: str,
) -> WSO2SCIMError:
    upstream_status_code = response.status_code
    status_code = upstream_status_code
    error_type = f"scim_{operation}_failed"
    message = "Authentication service unavailable"
    wso2_error_code = _safe_wso2_error_code(response)

    if upstream_status_code == HTTPStatus.BAD_REQUEST:
        message = (
            "Invalid registration request"
            if operation == "registration"
            else "Invalid WSO2 SCIM request"
        )
        error_type = f"scim_{operation}_bad_request"
    elif upstream_status_code == HTTPStatus.NOT_FOUND:
        message = "User not found"
        status_code = HTTPStatus.NOT_FOUND
        error_type = f"scim_{operation}_not_found"
    elif upstream_status_code == HTTPStatus.CONFLICT:
        message = "User already exists"
        error_type = f"scim_{operation}_conflict"
    elif upstream_status_code == HTTPStatus.UNAUTHORIZED:
        status_code = HTTPStatus.BAD_GATEWAY
        message = "WSO2 service credential error"
        error_type = f"scim_{operation}_credential_error"
    elif upstream_status_code == HTTPStatus.FORBIDDEN:
        status_code = HTTPStatus.FORBIDDEN
        message = "Insufficient WSO2 scope for this operation"
        error_type = f"scim_{operation}_forbidden"
    else:
        status_code = HTTPStatus.BAD_GATEWAY

    _log_wso2_event(
        "error",
        f"WSO2 {operation.replace('_', ' ')} failed",
        request_id=request_id,
        target_url=target_url,
        status_code=upstream_status_code,
        error_type=error_type,
        wso2_error_code=wso2_error_code,
    )
    return WSO2SCIMError(
        message,
        status_code=status_code,
        error_type=error_type,
        target_url=target_url,
        wso2_error_code=wso2_error_code,
    )


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------


async def _service_access_token(
    client: httpx.AsyncClient,
    *,
    scope: str,
    request_id: str | None = None,
) -> str:
    target_url = settings.wso2_token_url
    try:
        response = await client.post(
            target_url,
            data={
                "grant_type": "client_credentials",
                "scope": scope,
            },
            auth=_service_basic_auth(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    except httpx.HTTPError as exc:
        _log_wso2_event(
            "error",
            "WSO2 client_credentials token request was unavailable",
            request_id=request_id,
            target_url=target_url,
            error_type=exc.__class__.__name__,
        )
        raise WSO2SCIMError(
            "Authentication service unavailable",
            status_code=HTTPStatus.BAD_GATEWAY,
            error_type=exc.__class__.__name__,
            target_url=target_url,
        ) from exc
    if response.status_code >= 400:
        wso2_error_code = _safe_wso2_error_code(response)
        _log_wso2_event(
            "error",
            "WSO2 client_credentials token request failed",
            request_id=request_id,
            target_url=target_url,
            status_code=response.status_code,
            error_type="client_credentials_failed",
            wso2_error_code=wso2_error_code,
        )
        raise WSO2SCIMError(
            "WSO2 registration configuration error",
            status_code=HTTPStatus.BAD_GATEWAY,
            error_type="client_credentials_failed",
            target_url=target_url,
            wso2_error_code=wso2_error_code,
        )

    try:
        token = response.json().get("access_token")
    except ValueError as exc:
        _log_wso2_event(
            "error",
            "WSO2 token response was not valid JSON",
            request_id=request_id,
            target_url=target_url,
            status_code=response.status_code,
            error_type="invalid_json",
        )
        raise WSO2SCIMError(
            "WSO2 registration configuration error",
            status_code=HTTPStatus.BAD_GATEWAY,
            error_type="invalid_json",
            target_url=target_url,
        ) from exc

    if not token:
        _log_wso2_event(
            "error",
            "WSO2 token response did not include an access token",
            request_id=request_id,
            target_url=target_url,
            status_code=response.status_code,
            error_type="missing_access_token",
        )
        raise WSO2SCIMError(
            "WSO2 registration configuration error",
            status_code=HTTPStatus.BAD_GATEWAY,
            error_type="missing_access_token",
            target_url=target_url,
        )
    return str(token)


async def _service_request_headers(
    client: httpx.AsyncClient,
    *,
    scope: str,
    request_id: str | None = None,
) -> dict[str, str]:
    access_token = await _service_access_token(
        client,
        scope=scope,
        request_id=request_id,
    )
    return {"Authorization": f"Bearer {access_token}"}


# ---------------------------------------------------------------------------
# SCIM response normalization
# ---------------------------------------------------------------------------


def _email_from_scim_user(user: dict[str, Any], fallback: str) -> str:
    emails = user.get("emails")
    if isinstance(emails, list):
        for email in emails:
            if isinstance(email, dict) and email.get("primary") is True:
                return str(email.get("value") or fallback)
        for email in emails:
            if isinstance(email, dict) and email.get("value"):
                return str(email["value"])
    username = user.get("userName")
    if isinstance(username, str) and "@" in username:
        return username
    return fallback


def _roles_from_groups(groups: Any) -> list[str]:
    if not isinstance(groups, list):
        return []

    roles: list[str] = []
    for group in groups:
        if not isinstance(group, dict):
            continue
        role_name = (
            group.get("display") or group.get("displayName") or group.get("value")
        )
        if role_name:
            roles.append(str(role_name))
    return roles


def _roles_from_token(payload: dict[str, Any]) -> list[str]:
    claim = payload.get("roles") or payload.get("groups")
    if isinstance(claim, list):
        return [str(role) for role in claim if role]
    if isinstance(claim, str):
        return [role for role in claim.split() if role]
    return []


def _normalize_scim_user(resource: dict[str, Any]) -> dict[str, Any]:
    """Normalize a raw SCIM2 user resource into Wso2UserProfile-compatible dict."""
    user_id = str(resource.get("id") or "")
    if not user_id:
        raise WSO2SCIMError(
            "WSO2 user response has no id",
            status_code=HTTPStatus.BAD_GATEWAY,
            error_type="invalid_scim_user",
        )

    name = resource.get("name") or {}
    email = _email_from_scim_user(resource, "")
    roles = _roles_from_groups(resource.get("groups"))

    return {
        "id": user_id,
        "username": str(resource.get("userName") or email or user_id),
        "email": email or None,
        "first_name": name.get("givenName") if isinstance(name, dict) else None,
        "last_name": name.get("familyName") if isinstance(name, dict) else None,
        "active": bool(resource.get("active", True)),
        "roles": roles,
    }


def _scim_user_response(
    user: dict[str, Any],
    *,
    fallback_email: str,
    fallback_roles: list[str] | None = None,
) -> dict[str, Any]:
    user_id = str(user.get("id") or user.get("sub") or "")
    if not user_id:
        raise WSO2SCIMError("WSO2 user response has no id")

    roles = _roles_from_groups(user.get("groups"))
    if not roles and fallback_roles:
        roles = fallback_roles

    email = _email_from_scim_user(user, fallback_email)
    return {
        "user_id": user_id,
        "username": str(user.get("userName") or email),
        "email": email,
        "roles": roles,
    }


# ---------------------------------------------------------------------------
# Registration helpers
# ---------------------------------------------------------------------------


def _scim_create_user_payload(
    *,
    username: str,
    email: str,
    password: str,
    given_name: str,
    family_name: str,
) -> dict[str, Any]:
    return {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": username,
        "password": password,
        "name": {
            "givenName": given_name,
            "familyName": family_name,
        },
        "emails": [{"value": email, "primary": True}],
    }


def _register_user_response(
    user: dict[str, Any],
    *,
    fallback_username: str,
    fallback_email: str,
) -> dict[str, str]:
    user_id = str(user.get("id") or "")
    if not user_id:
        raise WSO2SCIMError("WSO2 user response has no id")

    return {
        "id": user_id,
        "username": str(user.get("userName") or fallback_username),
        "email": _email_from_scim_user(user, fallback_email),
        "message": "User registered successfully",
    }


async def register_wso2_user(
    *,
    username: str,
    email: str,
    password: str,
    given_name: str,
    family_name: str,
    request_id: str | None = None,
) -> dict[str, Any]:
    user_create_url = _scim_url("Users")
    async with httpx.AsyncClient(
        timeout=settings.wso2_request_timeout_seconds,
        verify=settings.wso2_verify_ssl,
    ) as client:
        headers = await _service_request_headers(
            client,
            scope=settings.wso2_scim_create_scope,
            request_id=request_id,
        )
        try:
            response = await client.post(
                user_create_url,
                json=_scim_create_user_payload(
                    username=username,
                    email=email,
                    password=password,
                    given_name=given_name,
                    family_name=family_name,
                ),
                headers={
                    **headers,
                    "Accept": "application/scim+json",
                    "Content-Type": "application/scim+json",
                },
            )
        except httpx.HTTPError as exc:
            _log_wso2_event(
                "error",
                "WSO2 SCIM user create endpoint was unavailable",
                request_id=request_id,
                target_url=user_create_url,
                error_type=exc.__class__.__name__,
            )
            raise WSO2SCIMError(
                "Authentication service unavailable",
                status_code=HTTPStatus.BAD_GATEWAY,
                error_type=exc.__class__.__name__,
                target_url=user_create_url,
            ) from exc

        if response.status_code >= 400:
            raise _raise_scim_error(
                operation="registration",
                response=response,
                request_id=request_id,
                target_url=user_create_url,
            )

        try:
            payload = response.json()
        except ValueError as exc:
            _log_wso2_event(
                "error",
                "WSO2 user registration returned invalid JSON",
                request_id=request_id,
                target_url=user_create_url,
                status_code=response.status_code,
                error_type="invalid_json",
            )
            raise WSO2SCIMError(
                "Authentication service unavailable",
                status_code=HTTPStatus.BAD_GATEWAY,
                error_type="invalid_json",
                target_url=user_create_url,
            ) from exc

    return _register_user_response(
        payload,
        fallback_username=username,
        fallback_email=email,
    )


# ---------------------------------------------------------------------------
# User lookup
# ---------------------------------------------------------------------------


async def get_wso2_user_by_id(
    user_id: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Fetch a single WSO2 user by SCIM2 id and return a normalized dict."""
    target_url = _scim_url(f"Users/{user_id}")
    async with httpx.AsyncClient(
        timeout=settings.wso2_request_timeout_seconds,
        verify=settings.wso2_verify_ssl,
    ) as client:
        headers = await _service_request_headers(
            client,
            scope=settings.wso2_scim_view_scope,
            request_id=request_id,
        )
        try:
            response = await client.get(
                target_url,
                headers=headers,
            )
        except httpx.HTTPError as exc:
            _log_wso2_event(
                "error",
                "WSO2 SCIM user lookup was unavailable",
                request_id=request_id,
                target_url=target_url,
                error_type=exc.__class__.__name__,
            )
            raise WSO2SCIMError(
                "Authentication service unavailable",
                status_code=HTTPStatus.BAD_GATEWAY,
                error_type=exc.__class__.__name__,
                target_url=target_url,
            ) from exc

    if response.status_code >= 400:
        raise _raise_scim_error(
            operation="lookup",
            response=response,
            request_id=request_id,
            target_url=target_url,
        )

    try:
        payload = response.json()
    except ValueError as exc:
        _log_wso2_event(
            "error",
            "WSO2 SCIM user lookup returned invalid JSON",
            request_id=request_id,
            target_url=target_url,
            status_code=response.status_code,
            error_type="invalid_json",
        )
        raise WSO2SCIMError(
            "Authentication service unavailable",
            status_code=HTTPStatus.BAD_GATEWAY,
            error_type="invalid_json",
            target_url=target_url,
        ) from exc

    normalized = _normalize_scim_user(payload)
    return {"user": normalized}


# ---------------------------------------------------------------------------
# User listing and search
# ---------------------------------------------------------------------------


def _escape_scim_filter_value(value: str) -> str:
    """Escape special characters in a SCIM filter string value."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


async def filter_wso2_users(
    *,
    filter_query: str | None = None,
    attributes: str | None = None,
    excluded_attributes: str | None = None,
    start_index: int = 1,
    count: int = 25,
    domain: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Query WSO2 SCIM2 GET /scim2/Users with optional filter/pagination."""
    target_url = _scim_url("Users")

    params: dict[str, str | int] = {
        "startIndex": start_index,
        "count": count,
    }
    if filter_query:
        params["filter"] = filter_query
    if attributes:
        params["attributes"] = attributes
    if excluded_attributes:
        params["excludedAttributes"] = excluded_attributes
    if domain:
        params["domain"] = domain

    async with httpx.AsyncClient(
        timeout=settings.wso2_request_timeout_seconds,
        verify=settings.wso2_verify_ssl,
    ) as client:
        headers = await _service_request_headers(
            client,
            scope=settings.wso2_scim_list_scope,
            request_id=request_id,
        )
        try:
            response = await client.get(
                target_url,
                params=params,
                headers=headers,
            )
        except httpx.HTTPError as exc:
            _log_wso2_event(
                "error",
                "WSO2 SCIM user list endpoint was unavailable",
                request_id=request_id,
                target_url=target_url,
                error_type=exc.__class__.__name__,
            )
            raise WSO2SCIMError(
                "Authentication service unavailable",
                status_code=HTTPStatus.BAD_GATEWAY,
                error_type=exc.__class__.__name__,
                target_url=target_url,
            ) from exc

    if response.status_code >= 400:
        raise _raise_scim_error(
            operation="list",
            response=response,
            request_id=request_id,
            target_url=target_url,
        )

    try:
        payload = response.json()
    except ValueError as exc:
        _log_wso2_event(
            "error",
            "WSO2 SCIM user list returned invalid JSON",
            request_id=request_id,
            target_url=target_url,
            status_code=response.status_code,
            error_type="invalid_json",
        )
        raise WSO2SCIMError(
            "Authentication service unavailable",
            status_code=HTTPStatus.BAD_GATEWAY,
            error_type="invalid_json",
            target_url=target_url,
        ) from exc

    resources = payload.get("Resources") or []
    if not isinstance(resources, list):
        resources = []
    users = [_normalize_scim_user(r) for r in resources if isinstance(r, dict)]

    return {
        "total_results": int(payload.get("totalResults", 0)),
        "start_index": int(payload.get("startIndex", 1)),
        "items_per_page": int(payload.get("itemsPerPage", len(users))),
        "users": users,
    }


async def search_wso2_users(
    *,
    query: str,
    start_index: int = 1,
    count: int = 25,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Build a safe SCIM filter from a keyword and delegate to filter_wso2_users."""
    escaped = _escape_scim_filter_value(query)
    scim_filter = f'userName co "{escaped}" or emails co "{escaped}"'
    return await filter_wso2_users(
        filter_query=scim_filter,
        start_index=start_index,
        count=count,
        request_id=request_id,
    )


# ---------------------------------------------------------------------------
# Token-based current-user resolution (used by gateway)
# ---------------------------------------------------------------------------


def _claim_email(payload: dict[str, Any]) -> str | None:
    for key in ("email", "preferred_username", "username", "user_name", "userName"):
        value = payload.get(key)
        if isinstance(value, str) and "@" in value:
            return value
    return None


def _claim_user_response(
    payload: dict[str, Any],
    *,
    user_id: str,
    roles: list[str],
) -> dict[str, Any] | None:
    email = _claim_email(payload)
    if not email:
        return None

    return {
        "user_id": user_id,
        "username": str(payload.get("username") or payload.get("user_name") or email),
        "email": email,
        "roles": roles,
    }


async def get_wso2_userinfo(
    access_token: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any] | None:
    target_url = settings.wso2_userinfo_url
    try:
        async with httpx.AsyncClient(
            timeout=settings.wso2_request_timeout_seconds,
            verify=settings.wso2_verify_ssl,
        ) as client:
            response = await client.get(
                target_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
    except httpx.HTTPError as exc:
        _log_wso2_event(
            "warning",
            "WSO2 userinfo endpoint was unavailable; falling back to SCIM lookup",
            request_id=request_id,
            target_url=target_url,
            error_type=exc.__class__.__name__,
        )
        return None

    if response.status_code >= 400:
        _log_wso2_event(
            "warning",
            "WSO2 userinfo endpoint returned an error; falling back to SCIM lookup",
            request_id=request_id,
            target_url=target_url,
            status_code=response.status_code,
            error_type="userinfo_failed",
            wso2_error_code=_safe_wso2_error_code(response),
        )
        return None

    try:
        payload = response.json()
    except ValueError:
        _log_wso2_event(
            "warning",
            "WSO2 userinfo endpoint returned invalid JSON; falling back to SCIM lookup",
            request_id=request_id,
            target_url=target_url,
            status_code=response.status_code,
            error_type="invalid_json",
        )
        return None

    return payload if isinstance(payload, dict) else None


async def current_wso2_user(
    token_payload: dict[str, Any],
    *,
    access_token: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    if token_payload.get("aut") != "APPLICATION_USER":
        raise WSO2SCIMError(
            "User token required",
            status_code=HTTPStatus.FORBIDDEN,
            error_type="user_token_required",
        )

    user_id = str(token_payload.get("sub") or "")
    if not user_id:
        raise WSO2SCIMError("Token payload has no subject")

    roles = _roles_from_token(token_payload)
    claim_response = _claim_user_response(token_payload, user_id=user_id, roles=roles)
    if claim_response is not None:
        return claim_response

    if access_token:
        userinfo = await get_wso2_userinfo(access_token, request_id=request_id)
        if userinfo is not None:
            claim_response = _claim_user_response(
                userinfo,
                user_id=str(userinfo.get("sub") or user_id),
                roles=roles,
            )
            if claim_response is not None:
                return claim_response

    detail = await get_wso2_user_by_id(user_id, request_id=request_id)
    user = detail["user"]
    return {
        "user_id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "roles": user["roles"],
    }
