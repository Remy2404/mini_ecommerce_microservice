from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class ProductResponse(BaseModel):
    product_id: UUID
    name: str
    description: str | None = None
    price: Decimal
    stock_quantity: int
    category: str
