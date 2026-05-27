import asyncio

from packages.config.settings import settings
from packages.contracts.payment.events import PaymentFailedEvent, PaymentSuccessEvent
from packages.contracts.common.schemas import OrderStatus
from packages.contracts.payment.topics import QueueName, RoutingKey
from packages.messaging.broker import broker, ecommerce_exchange, payment_result_queue
from packages.observability.logging import get_logger, setup_logging
from packages.observability.metrics import order_cancelled_total, order_confirmed_total
from packages.observability.tracing import add_span_attributes, setup_tracing
from packages.cache.valkey_client import get_valkey_client
from apps.order_service.app.application.services import save_order_status

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
    order_id = str(event.payload.order_id)

    add_span_attributes(
        {
            "order.id": order_id,
            "event.type": event.event_type,
        }
    )

    if event.event_type == RoutingKey.PAYMENT_SUCCESS:
        await save_order_status(
            order_id=order_id,
            status=OrderStatus.CONFIRMED,
        )

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

    await save_order_status(
        order_id=order_id,
        status=OrderStatus.CANCELLED,
    )

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
