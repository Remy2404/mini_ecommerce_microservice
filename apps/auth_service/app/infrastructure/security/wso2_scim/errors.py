from __future__ import annotations

from http import HTTPStatus


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
