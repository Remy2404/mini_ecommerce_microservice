from pydantic import Field, BaseModel
from decimal import Decimal

from uuid import UUID


class CreateProductRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(ge=0)
    stock_quantity: int = Field(ge=0)
    category: str = Field(min_length=1, max_length=100)


class ProductResponse(BaseModel):
    product_id: UUID
    name: str
    description: str | None = None
    price: Decimal
    stock_quantity: int
    category: str
