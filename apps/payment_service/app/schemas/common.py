from decimal import Decimal
from enum import StrEnum
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaymentStatus(StrEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: T | None = None


class PaymentResponse(BaseModel):
    payment_id: UUID
    order_id: UUID
    user_id: str
    status: PaymentStatus
    amount: Decimal = Field(ge=0)
    currency: str = "USD"
    failure_reason: str | None = None
