from decimal import Decimal
from enum import StrEnum
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class OrderStatus(StrEnum):
    PENDING = "PENDING"
    PAYMENT_PROCESSING = "PAYMENT_PROCESSING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class PaymentStatus(StrEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: UUID
    name: str
    description: str | None = None
    price: Decimal
    stock_quantity: int
    category: str


class CartItem(BaseModel):
    product_id: UUID
    name: str
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    subtotal: Decimal = Field(ge=0)


class CartResponse(BaseModel):
    cart_id: str
    user_id: str
    items: list[CartItem]
    total_amount: Decimal = Field(ge=0)


class OrderItem(BaseModel):
    product_id: UUID
    product_name: str
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    subtotal: Decimal = Field(ge=0)


class OrderResponse(BaseModel):
    order_id: UUID
    user_id: str
    cart_id: str
    status: OrderStatus
    total_amount: Decimal = Field(ge=0)
    currency: str = "USD"
    items: list[OrderItem]


class PaymentResponse(BaseModel):
    payment_id: UUID
    order_id: UUID
    user_id: str
    status: PaymentStatus
    amount: Decimal = Field(ge=0)
    currency: str = "USD"
    failure_reason: str | None = None


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: T | None = None


class ApiErrorResponse(BaseModel):
    success: bool = False
    error_code: str
    message: str
    details: dict[str, object] = Field(default_factory=dict)
