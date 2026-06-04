"""Product Service settings facade."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from .cache import CacheSettings
from .core import CoreSettings
from .database import DatabaseSettings
from .messaging import MessagingSettings
from .observability import ObservabilitySettings
from .payments import PaymentSettings
from .security import SecuritySettings
from .services import ServiceSettings
from .storage import StorageSettings
from .wso2 import WSO2Settings


class Settings(
    CoreSettings,
    MessagingSettings,
    WSO2Settings,
    DatabaseSettings,
    CacheSettings,
    ObservabilitySettings,
    ServiceSettings,
    SecuritySettings,
    PaymentSettings,
    StorageSettings,
    BaseSettings,
):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

__all__ = ["Settings", "get_settings", "settings"]
