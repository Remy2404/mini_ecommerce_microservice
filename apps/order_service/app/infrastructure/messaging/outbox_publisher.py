"""Durable outbox publisher for Order Service events."""

from packages.config.settings import settings
from packages.contracts.order.events import OrderCreatedEvent
from packages.observability.logging import get_logger

from apps.order_service.app.infrastructure.database.repository import (
    claim_pending_outbox_events,
    mark_outbox_event_failed,
    mark_outbox_event_published,
)
from apps.order_service.app.infrastructure.messaging.order_event_publisher import (
    publish_order_created,
)

logger = get_logger(__name__)


async def publish_pending_order_events(limit: int = 25) -> int:
    """Publish pending outbox events and mark their durable state."""
    published = 0
    for pending in await claim_pending_outbox_events(limit=limit):
        try:
            if pending.routing_key != settings.order_created_routing_key:
                raise ValueError(
                    f"Unsupported order outbox routing key: {pending.routing_key}"
                )

            await publish_order_created(
                OrderCreatedEvent.model_validate(pending.payload)
            )
            await mark_outbox_event_published(pending.event_id)
            published += 1
        except Exception as exc:
            await mark_outbox_event_failed(pending.event_id, str(exc))
            logger.exception(
                "Order outbox publish failed",
                event_id=pending.event_id,
                routing_key=pending.routing_key,
                attempts=pending.attempts,
            )

    return published
