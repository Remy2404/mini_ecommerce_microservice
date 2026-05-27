"""Compatibility exports for local JWT helpers."""

from packages.security.jwt import create_access_token, decode_access_token

__all__ = ["create_access_token", "decode_access_token"]
