"""Auth Service token security adapters."""

from apps.auth_service.app.infrastructure.security.tokens import issue_user_token

__all__ = ["issue_user_token"]
