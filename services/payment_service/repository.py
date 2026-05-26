"""Payment repository."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import text

from packages.config.settings import settings
from packages.database.session import transaction


async def save_payment(
    *,
    payment_id: UUID,
    order_id: UUID,
    user_id: str,
    status: str,
    amount: Decimal,
    currency: str,
    failure_reason: str | None,
    correlation_id: str,
) -> None:
    async with transaction(settings.payments_database_url) as connection:
        await connection.execute(
            text(
                """
                INSERT INTO payments (
                    id,
                    order_id,
                    user_id,
                    status,
                    amount,
                    currency,
                    failure_reason,
                    correlation_id
                )
                VALUES (
                    :id,
                    :order_id,
                    :user_id,
                    :status,
                    :amount,
                    :currency,
                    :failure_reason,
                    :correlation_id
                )
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    amount = EXCLUDED.amount,
                    currency = EXCLUDED.currency,
                    failure_reason = EXCLUDED.failure_reason,
                    correlation_id = EXCLUDED.correlation_id,
                    updated_at = CURRENT_TIMESTAMP
                """
            ),
            {
                "id": payment_id,
                "order_id": order_id,
                "user_id": user_id,
                "status": str(status),
                "amount": amount,
                "currency": currency,
                "failure_reason": failure_reason,
                "correlation_id": correlation_id,
            },
        )
