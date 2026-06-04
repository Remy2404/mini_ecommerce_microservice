"""Repository DTOs for payment persistence."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PendingOutboxEvent:
    event_id: str
    event_type: str
    routing_key: str
    payload: dict
    attempts: int
