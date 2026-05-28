import asyncio
import random
from uuid import uuid4

from packages.config.settings import settings
from packages.contracts.order.events import OrderCreatedEvent
from packages.contracts.payment.events import (
    PaymentFailedEvent,
    PaymentFailedPayload,
    PaymentSuccessEvent,
    PaymentSuccessPayload,
)
from packages.contracts.payment.topics import QueueName, RoutingKey
from packages.messaging.broker import broker, ecommerce_exchange, order_created_queue
from packages.messaging.retry import publish_retry_or_dlq
from packages.observability.logging import get_logger, setup_logging
from packages.observability.metrics import (
    payment_failed_total,
    payment_success_total,
    rabbitmq_message_consumed_total,
    rabbitmq_message_published_total,
)
from packages.observability.tracing import add_span_attributes, setup_tracing
from apps.payment_service.app.application.services import process_fake_payment
from apps.payment_service.app.infrastructure.cache.idempotency import (
    acquire_payment_event_lock,
)
from apps.payment_service.app.infrastructure.database.repository import (
    save_payment_with_outbox_once,
)
from apps.payment_service.app.infrastructure.messaging.outbox_publisher import (
    publish_pending_payment_events,
)

setup_logging(settings.payment_service_name)
setup_tracing(settings.payment_service_name)

logger = get_logger(__name__)


@broker.subscriber(
    queue=order_created_queue,
    exchange=ecommerce_exchange,
)
async def process_payment(event: OrderCreatedEvent) -> None:
    try:
        await _process_payment_once(event)
    except Exception as exc:
        await publish_retry_or_dlq(
            event=event,
            error=exc,
            retry_routing_key=RoutingKey.ORDER_CREATED_RETRY,
            dlq_routing_key=RoutingKey.ORDER_CREATED_DLQ,
            service_name=settings.payment_service_name,
        )


async def _process_payment_once(event: OrderCreatedEvent) -> None:
    lock_acquired = await acquire_payment_event_lock(event.event_id)
    if not lock_acquired:
        logger.info(
            "Duplicate order.created event skipped",
            event_id=event.event_id,
            order_id=str(event.payload.order_id),
        )
        return

    rabbitmq_message_consumed_total.labels(
        service_name=settings.payment_service_name,
        routing_key=RoutingKey.ORDER_CREATED,
    ).inc()

    logger.info(
        "Order created event received",
        order_id=str(event.payload.order_id),
        user_id=event.payload.user_id,
        amount=str(event.payload.amount),
    )

    await asyncio.sleep(
        random.uniform(
            settings.payment_min_delay_ms / 1000,
            settings.payment_max_delay_ms / 1000,
        )
    )

    decision = process_fake_payment(
        amount=event.payload.amount,
        random_value=random.random(),
    )
    is_success = decision.succeeded

    add_span_attributes(
        {
            "order.id": str(event.payload.order_id),
            "user.id": event.payload.user_id,
            "payment.success": is_success,
        }
    )

    if is_success:
        payment_id = uuid4()
        payment_event = PaymentSuccessEvent(
            correlation_id=event.correlation_id,
            trace_id=event.trace_id,
            payload=PaymentSuccessPayload(
                payment_id=payment_id,
                order_id=event.payload.order_id,
                user_id=event.payload.user_id,
                amount=event.payload.amount,
                currency=event.payload.currency,
            ),
        )

        saved = await save_payment_with_outbox_once(
            source_event_id=event.event_id,
            source_event_type=event.event_type,
            payment_id=payment_id,
            order_id=event.payload.order_id,
            user_id=event.payload.user_id,
            status=payment_event.payload.status,
            amount=event.payload.amount,
            currency=event.payload.currency,
            failure_reason=None,
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

        payment_success_total.labels(
            service_name=settings.payment_service_name,
        ).inc()

        rabbitmq_message_published_total.labels(
            service_name=settings.payment_service_name,
            routing_key=RoutingKey.PAYMENT_SUCCESS,
        ).inc()

        logger.info(
            "Payment success event published",
            order_id=str(event.payload.order_id),
            payment_id=str(payment_event.payload.payment_id),
            routing_key=RoutingKey.PAYMENT_SUCCESS,
        )

        return

    payment_id = uuid4()
    payment_event = PaymentFailedEvent(
        correlation_id=event.correlation_id,
        trace_id=event.trace_id,
        payload=PaymentFailedPayload(
            payment_id=payment_id,
            order_id=event.payload.order_id,
            user_id=event.payload.user_id,
            amount=event.payload.amount,
            currency=event.payload.currency,
            reason=decision.failure_reason or "Payment failed",
        ),
    )

    saved = await save_payment_with_outbox_once(
        source_event_id=event.event_id,
        source_event_type=event.event_type,
        payment_id=payment_id,
        order_id=event.payload.order_id,
        user_id=event.payload.user_id,
        status=payment_event.payload.status,
        amount=event.payload.amount,
        currency=event.payload.currency,
        failure_reason=payment_event.payload.reason,
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

    payment_failed_total.labels(
        service_name=settings.payment_service_name,
    ).inc()

    rabbitmq_message_published_total.labels(
        service_name=settings.payment_service_name,
        routing_key=RoutingKey.PAYMENT_FAILED,
    ).inc()

    logger.warning(
        "Payment failed event published",
        order_id=str(event.payload.order_id),
        payment_id=str(payment_event.payload.payment_id),
        routing_key=RoutingKey.PAYMENT_FAILED,
    )


async def main() -> None:
    logger.info(
        "Starting payment consumer service",
        queue=QueueName.ORDER_CREATED,
    )

    await broker.start()

    try:
        await asyncio.Event().wait()
    finally:
        await broker.close()


if __name__ == "__main__":
    asyncio.run(main())
