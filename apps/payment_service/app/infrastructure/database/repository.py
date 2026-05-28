"""Payment repository using SQLAlchemy async ORM."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import or_, select

from apps.payment_service.app.infrastructure.database.models import (
    InboxEvent,
    OutboxEvent,
    Payment,
)
from apps.payment_service.app.schemas.responses import PaymentResponse
from packages.config.settings import settings
from packages.database.session import session_scope


@dataclass(frozen=True)
class PendingOutboxEvent:
    event_id: str
    event_type: str
    routing_key: str
    payload: dict
    attempts: int


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

        session.add(
            InboxEvent(
                event_id=source_event_id,
                event_type=source_event_type,
                consumer_name=consumer_name,
            )
        )
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


async def claim_pending_outbox_events(limit: int = 25) -> list[PendingOutboxEvent]:
    now = datetime.now(UTC)
    async with session_scope(settings.payments_database_url) as session:
        result = await session.execute(
            select(OutboxEvent)
            .where(
                OutboxEvent.status.in_(("PENDING", "FAILED")),
                or_(
                    OutboxEvent.next_attempt_at.is_(None),
                    OutboxEvent.next_attempt_at <= now,
                ),
            )
            .order_by(OutboxEvent.created_at.asc())
            .limit(limit)
        )
        events = result.scalars().all()

        for event in events:
            event.status = "IN_PROGRESS"
            event.attempts += 1
            event.updated_at = now

        return [
            PendingOutboxEvent(
                event_id=event.event_id,
                event_type=event.event_type,
                routing_key=event.routing_key,
                payload=event.payload,
                attempts=event.attempts,
            )
            for event in events
        ]


async def mark_outbox_event_published(event_id: str) -> None:
    async with session_scope(settings.payments_database_url) as session:
        event = await session.get(OutboxEvent, event_id)
        if event is not None:
            event.status = "PUBLISHED"
            event.published_at = datetime.now(UTC)
            event.updated_at = datetime.now(UTC)


async def mark_outbox_event_failed(
    event_id: str,
    error: str,
    *,
    retry_delay_seconds: int = 30,
) -> None:
    async with session_scope(settings.payments_database_url) as session:
        event = await session.get(OutboxEvent, event_id)
        if event is not None:
            now = datetime.now(UTC)
            event.status = "FAILED"
            event.last_error = error[:1000]
            event.next_attempt_at = now + timedelta(seconds=retry_delay_seconds)
            event.updated_at = now


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
