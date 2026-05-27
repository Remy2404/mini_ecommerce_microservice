from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from apps.product_service.app.main import app
from apps.product_service.app.schemas import CategoryResponse


def test_create_category_endpoint_success() -> None:
    category_id = uuid4()
    category = CategoryResponse(
        category_id=category_id,
        name="electronics",
        description="Devices",
    )

    with patch(
        "apps.product_service.app.api.routes.create_category_for_catalog",
        new=AsyncMock(return_value=category),
    ):
        with TestClient(app) as client:
            response = client.post(
                "/categories",
                json={"name": "electronics", "description": "Devices"},
            )

    assert response.status_code == 201
    assert response.json()["data"]["category_id"] == str(category_id)
    assert response.json()["message"] == "Category created successfully"


def test_list_categories_endpoint_success() -> None:
    category = CategoryResponse(category_id=uuid4(), name="books")

    with patch(
        "apps.product_service.app.api.routes.find_categories",
        new=AsyncMock(return_value=[category]),
    ):
        with TestClient(app) as client:
            response = client.get("/categories")

    assert response.status_code == 200
    assert response.json()["data"][0]["name"] == "books"
