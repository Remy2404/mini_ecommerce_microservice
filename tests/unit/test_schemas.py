from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from apps.order_service.app.schemas.common import ApiResponse, OrderStatus
from apps.order_service.app.schemas.responses import OrderSummaryResponse
from apps.product_service.app.schemas.requests import CreateProductRequest


def test_order_summary_schema():
    order = OrderSummaryResponse(
        order_id=uuid4(),
        status=OrderStatus.PENDING,
    )

    assert order.status == OrderStatus.PENDING
    assert order.order_id is not None


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

