from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from apps.product_service.app.schemas.requests import CreateProductRequest
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


def test_create_product_request_rejects_negative_price() -> None:
    with pytest.raises(ValidationError):
        CreateProductRequest(
            name="Test Product",
            description=None,
            price=Decimal("-0.01"),
            stock_quantity=1,
            category="books",
        )
