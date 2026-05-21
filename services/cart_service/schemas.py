from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class AddCartItemRequest(BaseModel):
    user_id: str = Field(min_length=1)
    product_id: UUID
    name: str = Field(min_length=1, max_length=255)
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)


class CartItemResponse(BaseModel):
    product_id: UUID
    name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class CartResponse(BaseModel):
    user_id: str
    items: list[CartItemResponse]
    total_amount: Decimal
