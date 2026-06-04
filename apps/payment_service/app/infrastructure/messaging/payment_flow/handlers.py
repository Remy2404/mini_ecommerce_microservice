from __future__ import annotations

from apps.payment_service.app.domain.entities import Payment
from apps.payment_service.app.infrastructure.database.repository import (
    save_payment_with_outbox_once,
)
from apps.payment_service.app.infrastructure.messaging.outbox_publisher import (
    publish_pending_payment_events,
)
from apps.payment_service.app.infrastructure.observability.logging import (
    get_logger,
)
from apps.payment_service.app.infrastructure.observability.metrics import (
    payment_failed_total,
    payment_success_total,
    rabbitmq_message_published_total,
)
from apps.payment_service.app.schemas.events import (
    OrderCreatedEvent,
    PaymentFailedEvent,
    PaymentFailedPayload,
    PaymentSuccessEvent,
    PaymentSuccessPayload,
)
from apps.payment_service.app.schemas.topics import RoutingKey

logger = get_logger(__name__)


async def handle_success_payment(
    *,
    event: OrderCreatedEvent,
    payment: Payment,
) -> None:
    payment_event = PaymentSuccessEvent(
        correlation_id=event.correlation_id,
        trace_id=event.trace_id,
        payload=PaymentSuccessPayload(
            payment_id=payment.payment_id.value,
            order_id=event.payload.order_id,
            user_id=event.payload.user_id,
            amount=payment.amount.amount,
            currency=payment.amount.currency,
        ),
    )

    saved = await save_payment_with_outbox_once(
        source_event_id=event.event_id,
        source_event_type=event.event_type,
        payment_id=payment.payment_id.value,
        order_id=event.payload.order_id,
        user_id=event.payload.user_id,
        status=payment.status.value,
        amount=payment.amount.amount,
        currency=payment.amount.currency,
        failure_reason=payment.failure_reason,
        correlation_id=event.correlation_id,
        outbox_event_id=payment_event.event_id,
        outbox_event_type=payment_event.event_type,
        routing_key=RoutingKey.PAYMENT_SUCCESS,
        outbox_payload=payment_event.model_dump(mode="json"),
        trace_id=event.trace_id,
    )
    if not saved:
        logger.info(
            "Duplicate order.created event skipped by payment inbox",
            event_id=event.event_id,
            order_id=str(event.payload.order_id),
        )
        return

    await publish_pending_payment_events(limit=10)

    payment_success_total.labels(service_name="payment_service").inc()
    rabbitmq_message_published_total.labels(
        service_name="payment_service",
        routing_key=RoutingKey.PAYMENT_SUCCESS,
    ).inc()

    logger.info(
        "Payment success event published",
        order_id=str(event.payload.order_id),
        payment_id=str(payment.payment_id.value),
        routing_key=RoutingKey.PAYMENT_SUCCESS,
    )


async def handle_failure_payment(
    *,
    event: OrderCreatedEvent,
    payment: Payment,
) -> None:
    payment_event = PaymentFailedEvent(
        correlation_id=event.correlation_id,
        trace_id=event.trace_id,
        payload=PaymentFailedPayload(
            payment_id=payment.payment_id.value,
            order_id=event.payload.order_id,
            user_id=event.payload.user_id,
            amount=payment.amount.amount,
            currency=payment.amount.currency,
            reason=payment.failure_reason or "Payment failed",
        ),
    )

    saved = await save_payment_with_outbox_once(
        source_event_id=event.event_id,
        source_event_type=event.event_type,
        payment_id=payment.payment_id.value,
        order_id=event.payload.order_id,
        user_id=event.payload.user_id,
        status=payment.status.value,
        amount=payment.amount.amount,
        currency=payment.amount.currency,
        failure_reason=payment.failure_reason,
        correlation_id=event.correlation_id,
        outbox_event_id=payment_event.event_id,
        outbox_event_type=payment_event.event_type,
        routing_key=RoutingKey.PAYMENT_FAILED,
        outbox_payload=payment_event.model_dump(mode="json"),
        trace_id=event.trace_id,
    )
    if not saved:
        logger.info(
            "Duplicate order.created event skipped by payment inbox",
            event_id=event.event_id,
            order_id=str(event.payload.order_id),
        )
        return

    await publish_pending_payment_events(limit=10)

    payment_failed_total.labels(service_name="payment_service").inc()
    rabbitmq_message_published_total.labels(
        service_name="payment_service",
        routing_key=RoutingKey.PAYMENT_FAILED,
    ).inc()

    logger.warning(
        "Payment failed event published",
        order_id=str(event.payload.order_id),
        payment_id=str(payment.payment_id.value),
        routing_key=RoutingKey.PAYMENT_FAILED,
    )
