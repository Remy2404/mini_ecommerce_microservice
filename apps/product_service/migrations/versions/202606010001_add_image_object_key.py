"""Add image_object_key to products table.

Revision ID: product_202606010001
Revises: product_202605280001
Create Date: 2026-06-01 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "product_202606010001"
down_revision = "product_202605280001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("image_object_key", sa.String(length=512), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("products", "image_object_key")
