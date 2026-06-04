from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class OrderId:
    value: UUID

    @classmethod
    def new(cls) -> "OrderId":
        return cls(uuid4())

    @classmethod
    def from_value(cls, value: OrderId | UUID | str) -> "OrderId":
        if isinstance(value, OrderId):
            return value
        return cls(UUID(str(value)))

    def __str__(self) -> str:
        return str(self.value)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, OrderId):
            return self.value == other.value
        if isinstance(other, UUID):
            return self.value == other
        if isinstance(other, str):
            return str(self.value) == other
        return NotImplemented  # type: ignore[return-value]
