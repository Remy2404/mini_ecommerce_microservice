"""Payment Service routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from apps.payment_service.app.infrastructure.database.repository import get_payment
from apps.payment_service.app.schemas.responses import PaymentResponse
from packages.config.settings import settings
from packages.contracts.common.schemas import ApiResponse

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.payment_service_name}


@router.get("/payments/{payment_id}")
async def get_payment_endpoint(payment_id: UUID) -> ApiResponse[PaymentResponse]:
    payment = await get_payment(payment_id)
    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    return ApiResponse(
        success=True,
        message="Payment fetched successfully",
        data=payment,
    )
