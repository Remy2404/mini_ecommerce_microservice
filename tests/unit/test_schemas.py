from decimal import Decimal
from uuid import uuid4

from packages.contracts.schemas import ApiResponse, OrderResponse, OrderStatus


def test_order_response_schema():
    order = OrderResponse(
        order_id=uuid4(),
        user_id="user_123",
        cart_id="cart_user_123",
        status=OrderStatus.PENDING,
        total_amount=Decimal("99.98"),
        items=[],
    )

    assert order.status == OrderStatus.PENDING
    assert order.total_amount == Decimal("99.98")


def test_api_response_schema():
    response = ApiResponse[dict[str, str]](
        success=True,
        message="OK",
        data={"status": "ok"},
    )

    assert response.success is True
    assert response.data == {"status": "ok"}
