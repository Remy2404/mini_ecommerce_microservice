from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from packages.config.settings import settings
from services.product_service.main import app
from services.product_service.schemas import ProductResponse


def test_health_endpoint_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": settings.product_service_name}


def test_create_product_endpoint_success() -> None:
    product_id = uuid4()
    mock_product = ProductResponse(
        product_id=product_id,
        name="Test Product",
        description="A great product",
        price=99.99,
        stock_quantity=10,
        category="electronics",
    )

    with patch(
        "services.product_service.router.create_product",
        new=AsyncMock(return_value=mock_product),
    ):
        with TestClient(app) as client:
            response = client.post(
                "/products",
                json={
                    "name": "Test Product",
                    "description": "A great product",
                    "price": 99.99,
                    "stock_quantity": 10,
                    "category": "electronics",
                },
            )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Product created successfully"
    assert body["data"]["product_id"] == str(product_id)
    assert body["data"]["name"] == "Test Product"


def test_list_products_endpoint_success() -> None:
    product_id_1 = uuid4()
    product_id_2 = uuid4()
    mock_products = [
        ProductResponse(
            product_id=product_id_1,
            name="Product 1",
            price=19.99,
            stock_quantity=5,
            category="books",
        ),
        ProductResponse(
            product_id=product_id_2,
            name="Product 2",
            price=29.99,
            stock_quantity=3,
            category="books",
        ),
    ]

    with patch(
        "services.product_service.router.find_products",
        new=AsyncMock(return_value=mock_products),
    ):
        with TestClient(app) as client:
            response = client.get("/products")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]) == 2
    assert body["data"][0]["product_id"] == str(product_id_1)
    assert body["data"][1]["product_id"] == str(product_id_2)


def test_get_product_endpoint_success() -> None:
    product_id = uuid4()
    mock_product = ProductResponse(
        product_id=product_id,
        name="Test Product",
        price=49.99,
        stock_quantity=8,
        category="clothing",
    )

    with patch(
        "services.product_service.router.find_product",
        new=AsyncMock(return_value=mock_product),
    ):
        with TestClient(app) as client:
            response = client.get(f"/products/{product_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["product_id"] == str(product_id)
    assert body["data"]["name"] == "Test Product"


def test_get_product_endpoint_not_found() -> None:
    product_id = uuid4()

    with patch(
        "services.product_service.router.find_product",
        new=AsyncMock(return_value=None),
    ):
        with TestClient(app) as client:
            response = client.get(f"/products/{product_id}")

    assert response.status_code == 404
    body = response.json()
    assert body["detail"] == "Product not found"


def test_metrics_endpoint_returns_prometheus_data() -> None:
    with TestClient(app) as client:
        # Generate some traffic first
        client.get("/health")

        response = client.get("/metrics")

    assert response.status_code == 200
    assert "http_request_total" in response.text
