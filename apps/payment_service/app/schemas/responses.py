"""Payment Service response schemas."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PaymentResponse(BaseModel):
    payment_id: UUID
    order_id: UUID
    user_id: str
    status: str
    amount: Decimal = Field(ge=0)
    currency: str = "USD"
    failure_reason: str | None = None
