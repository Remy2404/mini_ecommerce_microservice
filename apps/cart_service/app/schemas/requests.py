from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AddCartItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: UUID
    quantity: int = Field(gt=0)
