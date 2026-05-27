from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


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
