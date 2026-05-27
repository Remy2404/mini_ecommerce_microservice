"""Auth Service application layer."""

from apps.auth_service.app.application.services import AuthService, get_auth_service

__all__ = ["AuthService", "get_auth_service"]
