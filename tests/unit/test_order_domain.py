from decimal import Decimal
from uuid import uuid4

import pytest

from apps.order_service.app.domain.entities import Order, OrderItemEntity
from apps.order_service.app.domain.exceptions import (
    EmptyCartError,
    InvalidStateTransitionException,
)
from apps.order_service.app.domain.value_objects import Money, OrderStatusState


def _item(*, amount: str = "50.00") -> OrderItemEntity:
    return OrderItemEntity(
        product_id=uuid4(),
        product_name="Widget",
        quantity=1,
        unit_price=Money(Decimal(amount)),
    )


def test_order_create_rejects_empty_cart() -> None:
    with pytest.raises(EmptyCartError, match="Cart is empty"):
        Order.create(
            user_id="user_123",
            cart_id="cart_user_123",
            total_amount=Money.zero(),
            items=(),
        )


def test_order_create_rejects_total_mismatch() -> None:
    with pytest.raises(ValueError, match="Order total must match item subtotals"):
        Order.create(
            user_id="user_123",
            cart_id="cart_user_123",
            total_amount=Money(Decimal("10.00")),
            items=(_item(amount="50.00"),),
        )


def test_order_state_machine_accepts_valid_transitions() -> None:
    order = Order.create(
        user_id="user_123",
        cart_id="cart_user_123",
        total_amount=Money(Decimal("50.00")),
        items=(_item(),),
    )

    order.pay()
    assert order.status == OrderStatusState.payment_processing()

    order.confirm()
    assert order.status == OrderStatusState.confirmed()


def test_order_state_machine_rejects_invalid_transition() -> None:
    order = Order.create(
        user_id="user_123",
        cart_id="cart_user_123",
        total_amount=Money(Decimal("50.00")),
        items=(_item(),),
    )
    order.confirm()

    with pytest.raises(
        InvalidStateTransitionException,
        match="Cannot transition order from CONFIRMED",
    ):
        order.fail()
