"""Order repository using SQLAlchemy async ORM."""

from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import delete, select

from apps.order_service.app.infrastructure.clients.cart_client import CartSnapshotItem
from apps.order_service.app.infrastructure.database.models import Order, OrderItem
from packages.config.settings import settings
from packages.database.session import session_scope


async def save_order(
    *,
    order_id: UUID,
    user_id: str,
    cart_id: str,
    status: str,
    total_amount: Decimal,
    currency: str,
    correlation_id: str,
    items: list[CartSnapshotItem],
) -> None:
    async with session_scope(settings.orders_database_url) as session:
        order = await session.get(Order, order_id)
        if order is None:
            order = Order(
                id=order_id,
                user_id=user_id,
                cart_id=cart_id,
                status=str(status),
                total_amount=total_amount,
                currency=currency,
                correlation_id=correlation_id,
            )
            session.add(order)
        else:
            order.status = str(status)
            order.total_amount = total_amount
            order.currency = currency
            order.correlation_id = correlation_id

        await session.execute(delete(OrderItem).where(OrderItem.order_id == order_id))
        for item in items:
            session.add(
                OrderItem(
                    id=uuid4(),
                    order_id=order_id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    subtotal=item.subtotal,
                )
            )


async def update_order_status(order_id: UUID, status: str) -> None:
    async with session_scope(settings.orders_database_url) as session:
        order = await session.get(Order, order_id)
        if order is not None:
            order.status = str(status)


async def get_order_status_by_id(order_id: UUID) -> str | None:
    async with session_scope(settings.orders_database_url) as session:
        order = await session.get(Order, order_id)

    return str(order.status) if order else None


async def list_order_statuses() -> dict[str, str]:
    async with session_scope(settings.orders_database_url) as session:
        result = await session.execute(
            select(Order).order_by(Order.created_at.desc(), Order.id.desc())
        )
        orders = result.scalars().all()

    return {str(order.id): str(order.status) for order in orders}


async def clear_orders() -> None:
    async with session_scope(settings.orders_database_url) as session:
        await session.execute(delete(Order))
