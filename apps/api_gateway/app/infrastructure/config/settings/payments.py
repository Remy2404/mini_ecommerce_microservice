"""Payment tuning settings."""

from pydantic import Field


class PaymentSettings:
    payment_success_rate: float = Field(..., validation_alias="PAYMENT_SUCCESS_RATE")
    payment_min_delay_ms: int = Field(..., validation_alias="PAYMENT_MIN_DELAY_MS")
    payment_max_delay_ms: int = Field(..., validation_alias="PAYMENT_MAX_DELAY_MS")
