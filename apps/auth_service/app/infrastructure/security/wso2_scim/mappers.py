from __future__ import annotations

from http import HTTPStatus
from typing import Any

from .errors import WSO2SCIMError


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


def _escape_scim_filter_value(value: str) -> str:
    """Escape special characters in a SCIM filter string value."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


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
