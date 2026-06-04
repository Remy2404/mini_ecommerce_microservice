"""OAuth error helpers shared by WSO2 token flows."""

from __future__ import annotations

from typing import Any

import httpx

CONFIGURATION_ERROR_CODES = frozenset(
    {
        "invalid_client",
        "unauthorized_client",
        "unsupported_grant_type",
    }
)


def oauth_error_code(response: httpx.Response) -> str:
    try:
        body: Any = response.json()
    except ValueError:
        return ""

    if not isinstance(body, dict):
        return ""

    error = body.get("error")
    return error if isinstance(error, str) else ""


def is_client_configuration_error(error_code: str) -> bool:
    return error_code in CONFIGURATION_ERROR_CODES
