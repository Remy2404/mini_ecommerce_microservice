import uuid

from .repository import OrderRepository
from .service import get_cart_data
from packages.messaging.broker import (
    broker,
    ecommerce_exchange,
)

from packages.config.settings import settings


async def start_order_saga(
    db,
    payload
):

    cart_response = await get_cart_data(
        payload.user_id
    )

    if not cart_response:
        raise Exception("Cart not found")

    cart = cart_response

    correlation_id = str(uuid.uuid4())

    order_data = {
        "user_id": payload.user_id,
        "cart_id": payload.cart_id,
        "status": "PENDING",
        "total_amount": cart["total_amount"],
        "shipping_address": payload.shipping_address,
        "correlation_id": correlation_id
    }

    order = await OrderRepository.create(
        db,
        order_data
    )

    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": settings.order_created_routing_key,
        "correlation_id": correlation_id,
        "order_id": str(order.id),
        "user_id": payload.user_id,
        "cart_id": payload.cart_id,
        "amount": cart["total_amount"]
    }

    await broker.publish(
    event,
    routing_key=settings.order_created_routing_key,
    exchange=ecommerce_exchange,
    )
    print("Published order.created event for order:", order.id)  # add this
    return order