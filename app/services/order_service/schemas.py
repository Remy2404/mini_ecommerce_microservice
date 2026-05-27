from pydantic import BaseModel, Field


class CreateOrderRequest(BaseModel):
    user_id: str = Field(min_length=1)
