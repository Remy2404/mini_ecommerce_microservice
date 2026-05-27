"""Payment repository using SQLAlchemy async ORM."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from apps.payment_service.app.infrastructure.database.models import Payment
from apps.payment_service.app.schemas.responses import PaymentResponse
from packages.config.settings import settings
from packages.database.session import session_scope


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
    async with session_scope(settings.payments_database_url) as session:
        payment = await session.get(Payment, payment_id)
        if payment is None:
            session.add(
                Payment(
                    id=payment_id,
                    order_id=order_id,
                    user_id=user_id,
                    status=str(status),
                    amount=amount,
                    currency=currency,
                    failure_reason=failure_reason,
                    correlation_id=correlation_id,
                )
            )
            return

        payment.status = str(status)
        payment.amount = amount
        payment.currency = currency
        payment.failure_reason = failure_reason
        payment.correlation_id = correlation_id


async def get_payment(payment_id: UUID) -> PaymentResponse | None:
    async with session_scope(settings.payments_database_url) as session:
        result = await session.execute(select(Payment).where(Payment.id == payment_id))
        payment = result.scalar_one_or_none()

    if payment is None:
        return None

    return PaymentResponse(
        payment_id=payment.id,
        order_id=payment.order_id,
        user_id=payment.user_id,
        status=payment.status,
        amount=payment.amount,
        currency=payment.currency,
        failure_reason=payment.failure_reason,
    )
