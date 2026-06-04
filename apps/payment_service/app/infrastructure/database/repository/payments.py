"""Payment aggregate persistence helpers."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from apps.payment_service.app.domain.entities import Payment as PaymentAggregate
from apps.payment_service.app.domain.value_objects import Money, PaymentStatusState
from apps.payment_service.app.infrastructure.config.settings import settings
from apps.payment_service.app.infrastructure.database.models import (
    InboxEvent,
    OutboxEvent,
    Payment,
)
from apps.payment_service.app.infrastructure.database.session import session_scope


@dataclass(slots=True)
class PaymentMapper:
    @staticmethod
    def from_primitives(
        *,
        payment_id: UUID,
        order_id: UUID,
        user_id: str,
        status: str,
        amount: Decimal,
        currency: str,
        failure_reason: str | None,
        correlation_id: str,
    ) -> PaymentAggregate:
        payment = PaymentAggregate.create(
            payment_id=payment_id,
            order_id=order_id,
            user_id=user_id,
            amount=Money(amount, currency),
            currency=currency,
            correlation_id=correlation_id,
        )
        desired_status = PaymentStatusState.from_value(status)
        if desired_status != payment.status:
            payment.transition_to(desired_status)
        payment.failure_reason = failure_reason.strip() if failure_reason else None
        return payment

    @staticmethod
    def to_domain(payment: Payment) -> PaymentAggregate:
        return PaymentAggregate(
            payment_id=payment.id,
            order_id=payment.order_id,
            user_id=payment.user_id,
            status=PaymentStatusState.from_value(payment.status),
            amount=Money(payment.amount, payment.currency),
            currency=payment.currency,
            failure_reason=payment.failure_reason,
            correlation_id=payment.correlation_id,
        )

    @staticmethod
    def to_model(payment: PaymentAggregate) -> Payment:
        return Payment(
            id=payment.payment_id.value,
            order_id=payment.order_id,
            user_id=payment.user_id,
            status=payment.status.value,
            amount=payment.amount.amount,
            currency=payment.amount.currency,
            failure_reason=payment.failure_reason,
            correlation_id=payment.correlation_id,
        )

    @staticmethod
    def sync_model(payment_model: Payment, payment: PaymentAggregate) -> None:
        payment_model.order_id = payment.order_id
        payment_model.user_id = payment.user_id
        payment_model.status = payment.status.value
        payment_model.amount = payment.amount.amount
        payment_model.currency = payment.amount.currency
        payment_model.failure_reason = payment.failure_reason
        payment_model.correlation_id = payment.correlation_id


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
        payment = PaymentMapper.from_primitives(
            payment_id=payment_id,
            order_id=order_id,
            user_id=user_id,
            status=status,
            amount=amount,
            currency=currency,
            failure_reason=failure_reason,
            correlation_id=correlation_id,
        )
        payment_model = await session.get(Payment, payment_id)
        if payment_model is None:
            session.add(PaymentMapper.to_model(payment))
            return

        PaymentMapper.sync_model(payment_model, payment)


async def save_payment_with_outbox_once(
    *,
    source_event_id: str,
    source_event_type: str,
    payment_id: UUID,
    order_id: UUID,
    user_id: str,
    status: str,
    amount: Decimal,
    currency: str,
    failure_reason: str | None,
    correlation_id: str,
    outbox_event_id: str,
    outbox_event_type: str,
    routing_key: str,
    outbox_payload: dict,
    trace_id: str | None,
    consumer_name: str = "payment.order_created_consumer",
) -> bool:
    async with session_scope(settings.payments_database_url) as session:
        if await session.get(InboxEvent, source_event_id) is not None:
            return False

        payment = PaymentMapper.from_primitives(
            payment_id=payment_id,
            order_id=order_id,
            user_id=user_id,
            status=status,
            amount=amount,
            currency=currency,
            failure_reason=failure_reason,
            correlation_id=correlation_id,
        )

        session.add(
            InboxEvent(
                event_id=source_event_id,
                event_type=source_event_type,
                consumer_name=consumer_name,
            )
        )
        session.add(PaymentMapper.to_model(payment))
        session.add(
            OutboxEvent(
                event_id=outbox_event_id,
                event_type=outbox_event_type,
                routing_key=routing_key,
                payload=outbox_payload,
                correlation_id=correlation_id,
                trace_id=trace_id,
            )
        )

    return True
