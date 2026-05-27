"""Order repository."""

from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import text

from packages.config.settings import settings
from packages.database.session import connect, transaction
from app.services.order_service.cart_reader import CartSnapshotItem


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
    async with transaction(settings.orders_database_url) as connection:
        await connection.execute(
            text(
                """
                INSERT INTO orders (
                    id,
                    user_id,
                    cart_id,
                    status,
                    total_amount,
                    currency,
                    correlation_id
                )
                VALUES (
                    :id,
                    :user_id,
                    :cart_id,
                    :status,
                    :total_amount,
                    :currency,
                    :correlation_id
                )
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    total_amount = EXCLUDED.total_amount,
                    currency = EXCLUDED.currency,
                    correlation_id = EXCLUDED.correlation_id,
                    updated_at = CURRENT_TIMESTAMP
                """
            ),
            {
                "id": order_id,
                "user_id": user_id,
                "cart_id": cart_id,
                "status": str(status),
                "total_amount": total_amount,
                "currency": currency,
                "correlation_id": correlation_id,
            },
        )

        await connection.execute(
            text("DELETE FROM order_items WHERE order_id = :order_id"),
            {"order_id": order_id},
        )

        for item in items:
            await connection.execute(
                text(
                    """
                    INSERT INTO order_items (
                        id,
                        order_id,
                        product_id,
                        product_name,
                        quantity,
                        unit_price,
                        subtotal
                    )
                    VALUES (
                        :id,
                        :order_id,
                        :product_id,
                        :product_name,
                        :quantity,
                        :unit_price,
                        :subtotal
                    )
                    """
                ),
                {
                    "id": uuid4(),
                    "order_id": order_id,
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "subtotal": item.subtotal,
                },
            )


async def update_order_status(order_id: UUID, status: str) -> None:
    async with transaction(settings.orders_database_url) as connection:
        await connection.execute(
            text(
                """
                UPDATE orders
                SET status = :status,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :order_id
                """
            ),
            {
                "order_id": order_id,
                "status": str(status),
            },
        )


async def get_order_status_by_id(order_id: UUID) -> str | None:
    async with connect(settings.orders_database_url) as connection:
        result = await connection.execute(
            text("SELECT status FROM orders WHERE id = :order_id"),
            {"order_id": order_id},
        )
        row = result.first()

    if row is None:
        return None

    return str(row._mapping["status"])


async def list_order_statuses() -> dict[str, str]:
    async with connect(settings.orders_database_url) as connection:
        result = await connection.execute(
            text(
                """
                SELECT id, status
                FROM orders
                ORDER BY created_at DESC, id DESC
                """
            )
        )
        rows = result.all()

    return {str(row._mapping["id"]): str(row._mapping["status"]) for row in rows}


async def clear_orders() -> None:
    async with transaction(settings.orders_database_url) as connection:
        await connection.execute(text("DELETE FROM orders"))
