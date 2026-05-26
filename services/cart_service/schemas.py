from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AddCartItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1)
    product_id: UUID
    quantity: int = Field(gt=0)


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
