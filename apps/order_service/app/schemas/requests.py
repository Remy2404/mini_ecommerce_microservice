from pydantic import BaseModel, ConfigDict


class CreateOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
