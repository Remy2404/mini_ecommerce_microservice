"""Helpers for parsing OAuth error payloads."""

from __future__ import annotations

import httpx


def oauth_error_code(response: httpx.Response) -> str | None:
    try:
        payload = response.json()
    except ValueError:
        return None

    if not isinstance(payload, dict):
        return None

    error = payload.get("error")
    return error if isinstance(error, str) else None


def is_client_configuration_error(error_code: str | None) -> bool:
    return error_code in {
        "unauthorized_client",
        "invalid_client",
        "unsupported_grant_type",
    }
