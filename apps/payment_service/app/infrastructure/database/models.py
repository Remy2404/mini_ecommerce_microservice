"""Payment Service SQLAlchemy ORM models."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from packages.database.session import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    correlation_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
