"""Payment router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from packages.database.session import get_db

from .repository import PaymentRepository

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)

@router.get("/")
async def list_payments(
    db: AsyncSession = Depends(get_db)
):

    payments = await PaymentRepository.get_all(db)

    return {
        "success": True,
        "message": "Payments fetched successfully",
        "data": [
            {
                "payment_id": payment.id,
                "order_id": payment.order_id,
                "user_id": payment.user_id,
                "amount": float(payment.amount),
                "status": payment.status
            }
            for payment in payments
        ]
    }


@router.get("/{payment_id}")
async def get_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db)
):

    payment = await PaymentRepository.get_by_id(
        db,
        payment_id
    )

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    return {
        "success": True,
        "message": "Payment fetched successfully",
        "data": {
            "payment_id": payment.id,
            "order_id": payment.order_id,
            "user_id": payment.user_id,
            "amount": float(payment.amount),
            "status": payment.status
        }
    }