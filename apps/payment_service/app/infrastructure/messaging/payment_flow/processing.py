from __future__ import annotations

import asyncio
import random
from uuid import uuid4

from apps.payment_service.app.application.services import process_fake_payment
from apps.payment_service.app.domain.entities import Payment
from apps.payment_service.app.infrastructure.cache.idempotency import (
    acquire_payment_event_lock,
)
from apps.payment_service.app.infrastructure.config.settings import settings
from apps.payment_service.app.infrastructure.messaging.broker import (
    broker,
    ecommerce_exchange,
    order_created_queue,
)
from apps.payment_service.app.infrastructure.messaging.payment_flow.handlers import (
    handle_failure_payment,
    handle_success_payment,
)
from apps.payment_service.app.infrastructure.messaging.retry import (
    publish_retry_or_dlq,
)
from apps.payment_service.app.infrastructure.observability.logging import (
    get_logger,
    setup_logging,
)
from apps.payment_service.app.infrastructure.observability.metrics import (
    rabbitmq_message_consumed_total,
)
from apps.payment_service.app.infrastructure.observability.tracing import (
    add_span_attributes,
    setup_tracing,
)
from apps.payment_service.app.schemas.events import OrderCreatedEvent
from apps.payment_service.app.schemas.topics import QueueName, RoutingKey

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
    payment = Payment.create(
        payment_id=uuid4(),
        order_id=event.payload.order_id,
        user_id=event.payload.user_id,
        amount=event.payload.amount,
        currency=event.payload.currency,
        correlation_id=event.correlation_id,
    )

    if decision.succeeded:
        payment.succeed()
    else:
        payment.fail(decision.failure_reason)

    add_span_attributes(
        {
            "order.id": str(event.payload.order_id),
            "user.id": event.payload.user_id,
            "payment.success": decision.succeeded,
        }
    )

    if decision.succeeded:
        await handle_success_payment(event=event, payment=payment)
        return

    await handle_failure_payment(event=event, payment=payment)


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
