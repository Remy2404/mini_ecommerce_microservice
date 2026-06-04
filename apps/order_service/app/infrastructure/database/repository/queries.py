from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from apps.order_service.app.infrastructure.config.settings import settings
from apps.order_service.app.infrastructure.database.models import Order as OrderModel
from apps.order_service.app.infrastructure.database.repository.mapper import OrderMapper
from apps.order_service.app.infrastructure.database.repository.types import (
    OrderRecord,
)
from apps.order_service.app.infrastructure.database.session import session_scope


async def get_order_status_by_id(order_id: UUID) -> str | None:
    async with session_scope(settings.orders_database_url) as session:
        result = await session.execute(
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(OrderModel.id == order_id)
        )
        order = result.scalar_one_or_none()

    return str(OrderMapper.to_domain(order).status) if order else None


async def get_order_record_by_id(order_id: UUID) -> OrderRecord | None:
    async with session_scope(settings.orders_database_url) as session:
        result = await session.execute(
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(OrderModel.id == order_id)
        )
        order = result.scalar_one_or_none()

    if order is None:
        return None

    aggregate = OrderMapper.to_domain(order)
    return OrderRecord(
        order_id=aggregate.order_id.value,
        user_id=aggregate.user_id,
        status=str(aggregate.status),
    )


async def list_order_statuses(user_id: str | None = None) -> dict[str, str]:
    async with session_scope(settings.orders_database_url) as session:
        query = select(OrderModel).options(selectinload(OrderModel.items))
        if user_id is not None:
            query = query.where(OrderModel.user_id == user_id)
        result = await session.execute(
            query.order_by(OrderModel.created_at.desc(), OrderModel.id.desc())
        )
        orders = result.scalars().all()

    return {
        str(OrderMapper.to_domain(order).order_id.value): str(
            OrderMapper.to_domain(order).status
        )
        for order in orders
    }


async def clear_orders() -> None:
    async with session_scope(settings.orders_database_url) as session:
        await session.execute(delete(OrderModel))
