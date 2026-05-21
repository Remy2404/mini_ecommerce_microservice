import asyncio
import random
from uuid import uuid4

from packages.config.settings import settings
from packages.contracts.events import (
    OrderCreatedEvent,
    PaymentFailedEvent,
    PaymentFailedPayload,
    PaymentSuccessEvent,
    PaymentSuccessPayload,
)
from packages.contracts.topics import (
    QueueName,
    RoutingKey,
)
from packages.messaging.broker import (
    broker,
    ecommerce_exchange,
    order_created_queue,
)
from packages.observability.logging import (
    get_logger,
    setup_logging,
)
from packages.observability.metrics import (
    payment_failed_total,
    payment_success_total,
    rabbitmq_message_consumed_total,
    rabbitmq_message_published_total,
)
from packages.observability.tracing import (
    add_span_attributes,
    setup_tracing,
)

setup_logging(settings.payment_service_name)
setup_tracing(settings.payment_service_name)

logger = get_logger(__name__)


@broker.subscriber(
    queue=order_created_queue,
    exchange=ecommerce_exchange,
)
@broker.publisher(
    exchange=ecommerce_exchange,
    routing_key=RoutingKey.PAYMENT_SUCCESS,
)
@broker.publisher(
    exchange=ecommerce_exchange,
    routing_key=RoutingKey.PAYMENT_FAILED,
)
async def process_payment(
    event: OrderCreatedEvent,
):
    rabbitmq_message_consumed_total.labels(
        service_name=settings.payment_service_name,
        routing_key=RoutingKey.ORDER_CREATED,
    ).inc()

    logger.info(
        "Order created event received",
        order_id=str(event.payload.order_id),
        user_id=event.payload.user_id,
    )

    await asyncio.sleep(
        random.uniform(1, 2),
    )

    is_success = random.random() <= settings.payment_success_rate

    add_span_attributes(
        {
            "order.id": str(event.payload.order_id),
            "user.id": event.payload.user_id,
            "payment.success": is_success,
        }
    )

    if is_success:
        payment_event = PaymentSuccessEvent(
            payload=PaymentSuccessPayload(
                payment_id=uuid4(),
                order_id=event.payload.order_id,
                user_id=event.payload.user_id,
                amount=event.payload.amount,
            )
        )

        payment_success_total.labels(
            service_name=settings.payment_service_name,
        ).inc()

        rabbitmq_message_published_total.labels(
            service_name=settings.payment_service_name,
            routing_key=RoutingKey.PAYMENT_SUCCESS,
        ).inc()

        logger.info(
            "Payment succeeded",
            order_id=str(event.payload.order_id),
            user_id=event.payload.user_id,
        )

        return payment_event

    payment_event = PaymentFailedEvent(
        payload=PaymentFailedPayload(
            payment_id=uuid4(),
            order_id=event.payload.order_id,
            user_id=event.payload.user_id,
            amount=event.payload.amount,
            reason="Insufficient balance",
        )
    )

    payment_failed_total.labels(
        service_name=settings.payment_service_name,
    ).inc()

    rabbitmq_message_published_total.labels(
        service_name=settings.payment_service_name,
        routing_key=RoutingKey.PAYMENT_FAILED,
    ).inc()

    logger.warning(
        "Payment failed",
        order_id=str(event.payload.order_id),
        user_id=event.payload.user_id,
    )

    return payment_event


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
