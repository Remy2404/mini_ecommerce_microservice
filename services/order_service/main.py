"""Order service entrypoint."""

import random
from decimal import Decimal
from uuid import uuid4

from fastapi import FastAPI, status

from packages.config.settings import settings
from packages.contracts.events import OrderCreatedEvent, OrderCreatedPayload
from packages.contracts.schemas import ApiResponse, OrderStatus
from packages.contracts.topics import RoutingKey
from packages.messaging.broker import broker, ecommerce_exchange
from packages.observability.logging import get_logger, setup_logging
from packages.observability.metrics import (
    order_created_total,
    rabbitmq_message_published_total,
)
from packages.observability.tracing import setup_tracing
from packages.observability.tracing import add_span_attributes

app = FastAPI(
    title="Order Service",
)

setup_logging(settings.order_service_name)
setup_tracing(settings.order_service_name, app)

logger = get_logger(__name__)


@app.on_event("startup")
async def startup() -> None:
    await broker.connect()

    logger.info("RabbitMQ broker connected")


@app.on_event("shutdown")
async def shutdown() -> None:
    await broker.close()

    logger.info("RabbitMQ broker disconnected")


@app.get("/health")
async def health() -> dict[str, str]:
    logger.info("Health check requested")

    return {
        "status": "ok",
        "service": settings.order_service_name,
    }


@app.post(
    "/orders",
    status_code=status.HTTP_201_CREATED,
)
async def create_order() -> ApiResponse[dict[str, str]]:
    order_id = uuid4()
    user_id = f"user_{random.randint(100, 999)}"
    cart_id = f"cart_{user_id}"

    amount = Decimal("99.98")

    event = OrderCreatedEvent(
        payload=OrderCreatedPayload(
            order_id=order_id,
            user_id=user_id,
            cart_id=cart_id,
            amount=amount,
        )
    )

    add_span_attributes(
        {
            "order.id": str(order_id),
            "user.id": user_id,
            "event.type": event.event_type,
        }
    )

    await broker.publish(
        message=event.model_dump(mode="json"),
        exchange=ecommerce_exchange,
        routing_key=RoutingKey.ORDER_CREATED,
    )

    order_created_total.labels(
        service_name=settings.order_service_name,
    ).inc()

    rabbitmq_message_published_total.labels(
        service_name=settings.order_service_name,
        routing_key=RoutingKey.ORDER_CREATED,
    ).inc()

    logger.info(
        "Order created event published",
        order_id=str(order_id),
        user_id=user_id,
        routing_key=RoutingKey.ORDER_CREATED,
    )

    return ApiResponse[dict[str, str]](
        success=True,
        message="Order created successfully",
        data={
            "order_id": str(order_id),
            "status": OrderStatus.PENDING,
        },
    )
