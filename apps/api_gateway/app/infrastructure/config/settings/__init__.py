"""Application settings."""

from functools import lru_cache

from apps.api_gateway.app.infrastructure.config.settings.base import GatewaySettingsBase
from apps.api_gateway.app.infrastructure.config.settings.cache import CacheSettings
from apps.api_gateway.app.infrastructure.config.settings.core import CoreSettings
from apps.api_gateway.app.infrastructure.config.settings.database import DatabaseSettings
from apps.api_gateway.app.infrastructure.config.settings.messaging import MessagingSettings
from apps.api_gateway.app.infrastructure.config.settings.observability import (
    ObservabilitySettings,
)
from apps.api_gateway.app.infrastructure.config.settings.payments import PaymentSettings
from apps.api_gateway.app.infrastructure.config.settings.security import SecuritySettings
from apps.api_gateway.app.infrastructure.config.settings.services import ServiceSettings
from apps.api_gateway.app.infrastructure.config.settings.storage import StorageSettings
from apps.api_gateway.app.infrastructure.config.settings.wso2 import WSO2Settings


class Settings(
    CoreSettings,
    ServiceSettings,
    WSO2Settings,
    DatabaseSettings,
    CacheSettings,
    ObservabilitySettings,
    SecuritySettings,
    PaymentSettings,
    StorageSettings,
    MessagingSettings,
    GatewaySettingsBase,
):
    """Application settings."""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

__all__ = ["Settings", "get_settings", "settings"]
