"""Payment repository."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Payment


class PaymentRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        payment: Payment
    ):
        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        return payment

    @staticmethod
    async def get_all(
        db: AsyncSession
    ):
        result = await db.execute(
            select(Payment)
        )

        return result.scalars().all()

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        payment_id: str
    ):
        result = await db.execute(
            select(Payment).where(
                Payment.id == payment_id
            )
        )

        return result.scalar_one_or_none()