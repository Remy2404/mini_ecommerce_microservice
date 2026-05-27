import asyncio

from packages.config.settings import settings
from packages.contracts.payment.events import PaymentFailedEvent, PaymentSuccessEvent
from packages.contracts.common.schemas import OrderStatus
from packages.contracts.payment.topics import QueueName, RoutingKey
from packages.messaging.broker import broker, ecommerce_exchange, payment_result_queue
from packages.messaging.retry import publish_retry_or_dlq
from packages.observability.logging import get_logger, setup_logging
from packages.observability.metrics import order_cancelled_total, order_confirmed_total
from packages.observability.tracing import add_span_attributes, setup_tracing
from packages.cache.valkey_client import get_valkey_client
from apps.order_service.app.infrastructure.database.repository import (
    apply_payment_result_once,
)

setup_logging(settings.order_service_name)
setup_tracing(settings.order_service_name)

logger = get_logger(__name__)


@broker.subscriber(
    queue=payment_result_queue,
    exchange=ecommerce_exchange,
)
async def handle_payment_result(
    event: PaymentSuccessEvent | PaymentFailedEvent,
) -> None:
    try:
        await _handle_payment_result_once(event)
    except Exception as exc:
        if event.event_type == RoutingKey.PAYMENT_SUCCESS:
            retry_routing_key = RoutingKey.PAYMENT_SUCCESS_RETRY
            dlq_routing_key = RoutingKey.PAYMENT_SUCCESS_DLQ
        else:
            retry_routing_key = RoutingKey.PAYMENT_FAILED_RETRY
            dlq_routing_key = RoutingKey.PAYMENT_FAILED_DLQ

        await publish_retry_or_dlq(
            event=event,
            error=exc,
            retry_routing_key=retry_routing_key,
            dlq_routing_key=dlq_routing_key,
            service_name=settings.order_service_name,
        )


async def _handle_payment_result_once(
    event: PaymentSuccessEvent | PaymentFailedEvent,
) -> None:
    order_id = str(event.payload.order_id)

    add_span_attributes(
        {
            "order.id": order_id,
            "event.type": event.event_type,
        }
    )

    if event.event_type == RoutingKey.PAYMENT_SUCCESS:
        processed = await apply_payment_result_once(
            event_id=event.event_id,
            event_type=event.event_type,
            order_id=event.payload.order_id,
            status=OrderStatus.CONFIRMED,
        )
        if not processed:
            logger.info(
                "Duplicate payment result event skipped",
                event_id=event.event_id,
                order_id=order_id,
            )
            return

        # Clear the user's cart on payment success
        try:
            valkey_client = get_valkey_client()
            valkey_client.delete(f"cart:{event.payload.user_id}")
            logger.info(
                "Cart cleared on payment success",
                user_id=event.payload.user_id,
                order_id=order_id,
            )
        except Exception as e:
            logger.error(
                "Failed to clear cart on payment success",
                user_id=event.payload.user_id,
                order_id=order_id,
                error=str(e),
            )

        order_confirmed_total.labels(
            service_name=settings.order_service_name,
        ).inc()

        logger.info(
            "Order confirmed after payment success",
            order_id=order_id,
            payment_id=str(event.payload.payment_id),
        )

        return

    processed = await apply_payment_result_once(
        event_id=event.event_id,
        event_type=event.event_type,
        order_id=event.payload.order_id,
        status=OrderStatus.CANCELLED,
    )
    if not processed:
        logger.info(
            "Duplicate payment result event skipped",
            event_id=event.event_id,
            order_id=order_id,
        )
        return

    order_cancelled_total.labels(
        service_name=settings.order_service_name,
    ).inc()

    logger.warning(
        "Order cancelled after payment failed",
        order_id=order_id,
        payment_id=str(event.payload.payment_id),
    )


async def main() -> None:
    logger.info(
        "Starting order payment-result consumer",
        queue=QueueName.PAYMENT_RESULT,
    )

    await broker.start()

    try:
        await asyncio.Event().wait()
    finally:
        await broker.close()


if __name__ == "__main__":
    asyncio.run(main())
