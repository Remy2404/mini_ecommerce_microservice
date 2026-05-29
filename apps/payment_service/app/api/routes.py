"""Payment Service routes."""

from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, status

from apps.payment_service.app.infrastructure.database.repository import get_payment
from apps.payment_service.app.schemas.responses import PaymentResponse
from packages.config.settings import settings
from packages.contracts.common.schemas import ApiResponse
from packages.security.headers import AUTHENTICATED_USER_ID_HEADER

router = APIRouter()


def _require_authenticated_user_id(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authenticated user",
        )
    return user_id


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.payment_service_name}


@router.get("/payments/{payment_id}")
async def get_payment_endpoint(
    payment_id: UUID,
    authenticated_user_id: str | None = Header(
        default=None,
        alias=AUTHENTICATED_USER_ID_HEADER,
    ),
) -> ApiResponse[PaymentResponse]:
    payment = await get_payment(payment_id)
    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    if payment.user_id != _require_authenticated_user_id(authenticated_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )

    return ApiResponse(
        success=True,
        message="Payment fetched successfully",
        data=payment,
    )
