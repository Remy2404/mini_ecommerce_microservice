from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Order


class OrderRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        order_data: dict
    ):

        order = Order(**order_data)

        db.add(order)

        await db.flush()
        await db.refresh(order)

        return order

    @staticmethod
    async def get_all(
        db: AsyncSession
    ):

        result = await db.execute(
            select(Order)
        )

        return result.scalars().all()

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        order_id: str
    ):

        result = await db.execute(
            select(Order).where(
                Order.id == order_id
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def update_status(
        db: AsyncSession,
        order_id: str,
        status: str
    ):

        order = await OrderRepository.get_by_id(
            db,
            order_id
        )

        if not order:
            return None

        order.status = status

        await db.flush()
        await db.refresh(order)

        return order