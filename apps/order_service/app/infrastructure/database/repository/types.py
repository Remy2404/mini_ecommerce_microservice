from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class PendingOutboxEvent:
    event_id: str
    event_type: str
    routing_key: str
    payload: dict
    attempts: int


@dataclass(frozen=True)
class OrderRecord:
    order_id: UUID
    user_id: str
    status: str
