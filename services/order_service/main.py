"""Order service entrypoint. main """

from uuid import uuid4

from fastapi import FastAPI, status, HTTPException

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
from services.order_service.state import (
    get_all_orders,
    get_order_status,
    save_order_status,
)
from services.order_service.cart_reader import (
    CartNotFoundError,
    EmptyCartError,
    get_cart_total_amount,
)
from services.order_service.schemas import CreateOrderRequest

from prometheus_client import make_asgi_app
from packages.observability.http_metrics import HTTPMetricsMiddleware

app = FastAPI(
    title="Order Service",
)

setup_logging(settings.order_service_name)
setup_tracing(settings.order_service_name, app)

app.mount("/metrics", make_asgi_app())
app.add_middleware(HTTPMetricsMiddleware, service_name=settings.order_service_name)

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
async def create_order(request: CreateOrderRequest) -> ApiResponse[dict[str, str]]:
    order_id = uuid4()
    user_id = request.user_id
    cart_id = f"cart_{user_id}"

    try:
        amount = get_cart_total_amount(user_id)
    except CartNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart not found",
        )
    except EmptyCartError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty",
        )

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

    save_order_status(
        order_id=str(order_id),
        status=OrderStatus.PENDING,
    )

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


@app.get('/orders/{order_id}')
async def get_order(order_id: str) -> ApiResponse[dict[str, str]]:
    order_status = get_order_status(order_id)

    if order_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    return ApiResponse[dict[str, str]](
        success=True,
        message='Order fetched successfully',
        data={
            'order_id': order_id,
            'status': order_status,
        },
    )


@app.get('/orders')
async def list_orders() -> ApiResponse[dict[str, str]]:
    return ApiResponse[dict[str, str]](
        success=True,
        message='Orders fetched successfully',
        data=get_all_orders(),
)
