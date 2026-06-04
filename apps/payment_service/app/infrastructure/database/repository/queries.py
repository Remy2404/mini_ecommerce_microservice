"""Payment query helpers."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from apps.payment_service.app.infrastructure.config.settings import settings
from apps.payment_service.app.infrastructure.database.models import Payment
from apps.payment_service.app.infrastructure.database.repository.payments import (
    PaymentMapper,
)
from apps.payment_service.app.infrastructure.database.session import session_scope
from apps.payment_service.app.schemas.responses import PaymentResponse


async def get_payment(payment_id: UUID) -> PaymentResponse | None:
    async with session_scope(settings.payments_database_url) as session:
        result = await session.execute(select(Payment).where(Payment.id == payment_id))
        payment_model = result.scalar_one_or_none()

    if payment_model is None:
        return None

    payment = PaymentMapper.to_domain(payment_model)
    return PaymentResponse(
        payment_id=payment.payment_id.value,
        order_id=payment.order_id,
        user_id=payment.user_id,
        status=payment.status.value,
        amount=payment.amount.amount,
        currency=payment.amount.currency,
        failure_reason=payment.failure_reason,
    )
