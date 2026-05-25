"""Order router."""

from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from packages.config.settings import settings
from packages.contracts.events import OrderCreatedEvent, OrderCreatedPayload
from packages.contracts.schemas import ApiResponse, OrderStatus
from packages.contracts.topics import RoutingKey
from packages.observability.logging import get_logger
from packages.observability.metrics import (
	order_created_total,
	rabbitmq_message_published_total,
)
from packages.observability.tracing import add_span_attributes
from services.order_service.cart_reader import (
	CartNotFoundError,
	EmptyCartError,
)
from services.order_service.schemas import CreateOrderRequest
from services.order_service import main as order_main

router = APIRouter()

logger = get_logger(__name__)


@router.get("/health")
async def health() -> dict[str, str]:
	logger.info("Health check requested")

	return {
		"status": "ok",
		"service": settings.order_service_name,
	}


@router.post(
	"/orders",
	status_code=status.HTTP_201_CREATED,
)
async def create_order(request: CreateOrderRequest) -> ApiResponse[dict[str, str]]:
	order_id = uuid4()
	user_id = request.user_id
	cart_id = f"cart_{user_id}"

	try:
		amount = order_main.get_cart_total_amount(user_id)
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

	await order_main.broker.publish(
		message=event.model_dump(mode="json"),
		exchange=order_main.ecommerce_exchange,
		routing_key=RoutingKey.ORDER_CREATED,
	)

	order_created_total.labels(
		service_name=settings.order_service_name,
	).inc()

	rabbitmq_message_published_total.labels(
		service_name=settings.order_service_name,
		routing_key=RoutingKey.ORDER_CREATED,
	).inc()

	order_main.save_order_status(
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


@router.get("/orders/{order_id}")
async def get_order(order_id: str) -> ApiResponse[dict[str, str]]:
	order_status = order_main.get_order_status(order_id)

	if order_status is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Order not found",
		)

	return ApiResponse[dict[str, str]](
		success=True,
		message="Order fetched successfully",
		data={
			"order_id": order_id,
			"status": order_status,
		},
	)


@router.get("/orders")
async def list_orders() -> ApiResponse[dict[str, str]]:
	return ApiResponse[dict[str, str]](
		success=True,
		message="Orders fetched successfully",
		data=order_main.get_all_orders(),
	)
