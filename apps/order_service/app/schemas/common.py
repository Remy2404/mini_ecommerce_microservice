from decimal import Decimal
from enum import StrEnum
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

T = TypeVar("T")


class OrderStatus(StrEnum):
    PENDING = "PENDING"
    PAYMENT_PROCESSING = "PAYMENT_PROCESSING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class PaymentStatus(StrEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: T | None = None


class OrderItemResponse(BaseModel):
    product_id: UUID
    product_name: str
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    subtotal: Decimal = Field(ge=0)


class OrderSummaryResponse(BaseModel):
    order_id: UUID
    status: str


class CartSnapshotItem(BaseModel):
    product_id: UUID
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class CartSnapshot(BaseModel):
    cart_id: str
    total_amount: Decimal
    items: list[CartSnapshotItem]
