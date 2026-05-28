"""Order Service response schemas."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class OrderItemResponse(BaseModel):
    product_id: UUID
    product_name: str
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    subtotal: Decimal = Field(ge=0)


class OrderSummaryResponse(BaseModel):
    order_id: UUID
    status: str
