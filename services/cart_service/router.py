"""Cart router."""

from uuid import UUID

from fastapi import APIRouter, status

from packages.config.settings import settings
from packages.contracts.schemas import ApiResponse
from packages.observability.logging import get_logger
from packages.observability.tracing import add_span_attributes
from services.cart_service.schemas import AddCartItemRequest, CartResponse
from services.cart_service import main as cart_main

router = APIRouter()

logger = get_logger(__name__)


@router.get("/health")
async def health() -> dict[str, str]:
	logger.info("Health check requested")

	return {
		"status": "ok",
		"service": settings.cart_service_name,
	}


@router.post(
	"/cart/items",
	status_code=status.HTTP_201_CREATED,
)
async def add_cart_item(
	request: AddCartItemRequest,
) -> ApiResponse[CartResponse]:
	cart = cart_main.add_item_to_cart(request)

	add_span_attributes(
		{
			"user.id": request.user_id,
			"product.id": str(request.product_id),
			"cart.items_count": len(cart.items),
		}
	)

	logger.info(
		"Cart item added",
		user_id=request.user_id,
		product_id=str(request.product_id),
		quantity=request.quantity,
	)

	return ApiResponse[CartResponse](
		success=True,
		message="Item added to cart",
		data=cart,
	)


@router.get("/cart/{user_id}")
async def get_cart_endpoint(user_id: str) -> ApiResponse[CartResponse]:
	cart = cart_main.find_cart(user_id)

	logger.info(
		"Cart fetched",
		user_id=user_id,
		items_count=len(cart.items),
	)

	return ApiResponse[CartResponse](
		success=True,
		message="Cart fetched successfully",
		data=cart,
	)


@router.delete("/cart/{user_id}/items/{product_id}")
async def remove_cart_item_endpoint(
	user_id: str,
	product_id: UUID,
) -> ApiResponse[CartResponse]:
	cart = cart_main.delete_cart_item(
		user_id=user_id,
		product_id=product_id,
	)

	logger.info(
		"Cart item removed",
		user_id=user_id,
		product_id=str(product_id),
	)

	return ApiResponse[CartResponse](
		success=True,
		message="Item removed from cart",
		data=cart,
	)


@router.delete("/cart/{user_id}")
async def clear_cart_endpoint(user_id: str) -> ApiResponse[dict[str, str]]:
	cart_main.delete_cart(user_id)

	logger.info(
		"Cart cleared",
		user_id=user_id,
	)

	return ApiResponse[dict[str, str]](
		success=True,
		message="Cart cleared successfully",
		data={
			"user_id": user_id,
		},
	)
