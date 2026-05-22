from pydantic import BaseModel
from typing import List


class OrderItem(BaseModel):

    product_id: str
    name: str
    quantity: int
    unit_price: float
    subtotal: float


class CreateOrderRequest(BaseModel):

    user_id: str
    cart_id: str
    shipping_address: str


class OrderResponse(BaseModel):

    order_id: str
    status: str
    total_amount: float