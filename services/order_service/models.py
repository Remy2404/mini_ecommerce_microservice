from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import DateTime

from packages.database.primary import Base


class Order(Base):

    __tablename__ = "orders"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid4())
    )

    user_id = Column(
        String,
        nullable=False
    )

    cart_id = Column(
        String,
        nullable=False
    )

    status = Column(
        String,
        nullable=False,
        default="PENDING"
    )

    total_amount = Column(
        Float,
        nullable=False
    )

    shipping_address = Column(
        String,
        nullable=False
    )

    correlation_id = Column(
        String,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )