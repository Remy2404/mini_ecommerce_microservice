"""Order router."""

from fastapi import APIRouter, HTTPException, status

from packages.config.settings import settings
from packages.contracts.common.schemas import ApiResponse
from packages.observability.logging import get_logger
from apps.order_service.app.domain.exceptions import (
    CartNotFoundError,
    EmptyCartError,
)
from apps.order_service.app.schemas.requests import CreateOrderRequest
from apps.order_service.app.application.services import (
    create_order_for_user,
    get_all_orders,
    get_order_status,
)

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
    try:
        created_order = await create_order_for_user(request.user_id)
    except CartNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart not found",
        ) from exc
    except EmptyCartError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty",
        ) from exc

    return ApiResponse[dict[str, str]](
        success=True,
        message="Order created successfully",
        data={
            "order_id": created_order.order_id,
            "status": created_order.status,
        },
    )


@router.get("/orders/{order_id}")
async def get_order(order_id: str) -> ApiResponse[dict[str, str]]:
    order_status = await get_order_status(order_id)

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
        data=await get_all_orders(),
    )
