"""Cart schemas."""
from pydantic import BaseModel
from typing import List

class CartItem(BaseModel):
    product_id: str
    name: str
    quantity: int
    unit_price: float
    subtotal: float

class Cart(BaseModel):
    cart_id: str
    user_id: str
    items: List[CartItem]
    total_amount: float
    
    