"""API Gateway configuration."""

from apps.api_gateway.app.infrastructure.config.settings import (
    Settings,
    get_settings,
    settings,
)

__all__ = ["Settings", "get_settings", "settings"]
