"""Add order outbox and inbox tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "order_202605280002"
down_revision = "order_202605280001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "outbox_events",
        sa.Column("event_id", sa.String(length=120), primary_key=True),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("routing_key", sa.String(length=120), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("correlation_id", sa.String(length=255), nullable=True),
        sa.Column("trace_id", sa.String(length=255), nullable=True),
        sa.Column(
            "status", sa.String(length=40), nullable=False, server_default="PENDING"
        ),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_order_outbox_event_type", "outbox_events", ["event_type"])
    op.create_index("ix_order_outbox_routing_key", "outbox_events", ["routing_key"])
    op.create_index("ix_order_outbox_status", "outbox_events", ["status"])
    op.create_index(
        "ix_order_outbox_correlation_id", "outbox_events", ["correlation_id"]
    )

    op.create_table(
        "inbox_events",
        sa.Column("event_id", sa.String(length=120), primary_key=True),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("consumer_name", sa.String(length=120), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_order_inbox_event_type", "inbox_events", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_order_inbox_event_type", table_name="inbox_events")
    op.drop_table("inbox_events")
    op.drop_index("ix_order_outbox_correlation_id", table_name="outbox_events")
    op.drop_index("ix_order_outbox_status", table_name="outbox_events")
    op.drop_index("ix_order_outbox_routing_key", table_name="outbox_events")
    op.drop_index("ix_order_outbox_event_type", table_name="outbox_events")
    op.drop_table("outbox_events")
