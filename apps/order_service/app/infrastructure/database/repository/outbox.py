from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select

from apps.order_service.app.infrastructure.config.settings import settings
from apps.order_service.app.infrastructure.database.models import OutboxEvent
from apps.order_service.app.infrastructure.database.repository.types import (
    PendingOutboxEvent,
)
from apps.order_service.app.infrastructure.database.session import session_scope


async def claim_pending_outbox_events(limit: int = 25) -> list[PendingOutboxEvent]:
    now = datetime.now(UTC)
    async with session_scope(settings.orders_database_url) as session:
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
    async with session_scope(settings.orders_database_url) as session:
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
    async with session_scope(settings.orders_database_url) as session:
        event = await session.get(OutboxEvent, event_id)
        if event is not None:
            now = datetime.now(UTC)
            event.status = "FAILED"
            event.last_error = error[:1000]
            event.next_attempt_at = now + timedelta(seconds=retry_delay_seconds)
            event.updated_at = now
