"""Durable outbox publisher for Payment Service events."""

from packages.contracts.payment.events import PaymentFailedEvent, PaymentSuccessEvent
from packages.contracts.payment.topics import RoutingKey
from packages.messaging.broker import broker, ecommerce_exchange
from packages.observability.logging import get_logger

from apps.payment_service.app.infrastructure.database.repository import (
    claim_pending_outbox_events,
    mark_outbox_event_failed,
    mark_outbox_event_published,
)

logger = get_logger(__name__)


async def publish_pending_payment_events(limit: int = 25) -> int:
    """Publish pending payment outbox events and persist delivery state."""
    published = 0
    for pending in await claim_pending_outbox_events(limit=limit):
        try:
            if pending.routing_key == RoutingKey.PAYMENT_SUCCESS:
                event = PaymentSuccessEvent.model_validate(pending.payload)
            elif pending.routing_key == RoutingKey.PAYMENT_FAILED:
                event = PaymentFailedEvent.model_validate(pending.payload)
            else:
                raise ValueError(
                    f"Unsupported payment outbox routing key: {pending.routing_key}"
                )

            await broker.publish(
                message=event.model_dump(mode="json"),
                exchange=ecommerce_exchange,
                routing_key=pending.routing_key,
            )
            await mark_outbox_event_published(pending.event_id)
            published += 1
        except Exception as exc:
            await mark_outbox_event_failed(pending.event_id, str(exc))
            logger.exception(
                "Payment outbox publish failed",
                event_id=pending.event_id,
                routing_key=pending.routing_key,
                attempts=pending.attempts,
            )

    return published
