import os
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from apps.product_service.app.main import app
from apps.product_service.app.infrastructure.database.repository import _product_response
from packages.storage.object_storage import UploadedObject


@pytest.fixture(autouse=True)
def _override_settings_env(monkeypatch):
    # Ensure upload size limits small for tests
    monkeypatch.setenv("THUMBNAIL_MAX_WIDTH", "300")
    monkeypatch.setenv("THUMBNAIL_MAX_HEIGHT", "300")
    yield


def _small_png_bytes() -> bytes:
    # A tiny 1x1 PNG
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02"
        b"\x00\x00\x00\x90wS\xde\x00\x00\x00\x0bIDAT\x08\xd7c``\x00\x00\x00\x05\x00\x01\xe2'\xbc\x33\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def test_product_response_builds_image_url_from_persisted_object_key(monkeypatch) -> None:
    monkeypatch.setattr(
        "apps.product_service.app.infrastructure.database.repository.build_public_url",
        lambda object_key: f"https://media.example/{object_key}",
    )
    product = SimpleNamespace(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        name="Wireless Mouse",
        description="Ergonomic USB-C mouse",
        price="19.99",
        stock_quantity=50,
        category=SimpleNamespace(name="Electronics"),
        image_object_key="products/mouse.webp",
    )

    response = _product_response(product)

    assert response.image_url == "https://media.example/products/mouse.webp"


def test_upload_image_unauthorized() -> None:
    with TestClient(app) as client:
        response = client.put(
            "/products/00000000-0000-0000-0000-000000000000/image",
            files={"file": ("img.png", _small_png_bytes(), "image/png")},
        )

    assert response.status_code == 401


def test_upload_image_invalid_bytes(monkeypatch) -> None:
    # Patch process_image_bytes to raise validation error
    from packages.storage.image_processor import ImageValidationError

    async def _fake_validate(token):
        return {"sub": "user-1", "scope": "openid profile product_image_write"}

    with patch("packages.storage.image_processor.process_image_bytes", side_effect=ImageValidationError("Invalid image")):
        with patch("packages.security.jwt_validator.validate_wso2_access_token", new=_fake_validate):
            with TestClient(app) as client:
                response = client.put(
                    "/products/00000000-0000-0000-0000-000000000000/image",
                    headers={"Authorization": "Bearer faketoken"},
                    files={"file": ("img.png", b"not an image", "image/png")},
                )

    assert response.status_code == 500


def test_upload_image_success_triggers_cleanup(monkeypatch):
    # Prepare mocks
    processed_buf = BytesIO(b"webpdata")
    processed_buf.seek(0)
    uploaded = UploadedObject(bucket_name="b", object_key="products/1.webp", content_type="image/webp", url="https://example.com/products/1.webp")

    async def _fake_validate(token):
        return {"sub": "user-1", "scope": "openid profile product_image_write"}

    monkeypatch.setattr("packages.storage.image_processor.process_image_bytes", lambda data: (processed_buf, "image/webp"))
    monkeypatch.setattr("packages.storage.image_processor.build_image_object_key", lambda prefix, ct: "products/1.webp")

    class FakeStorage:
        def __init__(self):
            self.deleted = []

        def upload_fileobj(self, file_buffer, object_key, content_type):
            return uploaded

        def build_public_url(self, object_key):
            return uploaded.url

        def delete_object(self, object_key):
            self.deleted.append(object_key)

    fake_storage = FakeStorage()

    async def fake_update_product_image(product_id, new_object_key):
        return "products/old.webp"

    monkeypatch.setattr("packages.storage.object_storage.get_object_storage_client", lambda: fake_storage)
    monkeypatch.setattr("apps.product_service.app.infrastructure.database.repository.update_product_image", AsyncMock(side_effect=fake_update_product_image))
    # monkeypatch.setattr uses (target, value) signature; don't pass 'new=' here
    monkeypatch.setattr("packages.security.jwt_validator.validate_wso2_access_token", _fake_validate)

    with TestClient(app) as client:
        response = client.put(
            "/products/00000000-0000-0000-0000-000000000000/image",
            headers={"Authorization": "Bearer faketoken"},
            files={"file": ("img.png", _small_png_bytes(), "image/png")},
        )

    assert response.status_code == 200
    assert response.json()["data"]["image_url"] == uploaded.url
    # Old key should have been deleted
    assert "products/old.webp" in fake_storage.deleted


def test_upload_image_forbidden_without_required_scope() -> None:
    async def _fake_validate(token):
        return {"sub": "user-1", "scope": "openid profile email"}

    with patch("packages.security.jwt_validator.validate_wso2_access_token", new=_fake_validate):
        with TestClient(app) as client:
            response = client.put(
                "/products/00000000-0000-0000-0000-000000000000/image",
                headers={"Authorization": "Bearer faketoken"},
                files={"file": ("img.png", _small_png_bytes(), "image/png")},
            )

    assert response.status_code == 403
    assert response.json()["detail"] == {
        "error_code": "FORBIDDEN",
        "message": "Missing required scope",
        "details": {"required_scope": "product_image_write"},
    }


@pytest.mark.skipif(os.environ.get("RUN_MINIO_INTEGRATION") != "true", reason="MinIO integration not enabled")
def test_minio_integration_upload_and_delete():
    # This test requires a running MinIO instance and valid settings in env
    from packages.storage.object_storage import get_object_storage_client

    client = get_object_storage_client()
    data = _small_png_bytes()
    # Process using real processor
    from packages.storage.image_processor import process_image_bytes

    processed_buf, content_type = process_image_bytes(data)
    object_key = f"tests/{os.getpid()}_integration.webp"

    uploaded = client.upload_fileobj(processed_buf, object_key, content_type)
    assert uploaded.object_key == object_key
    assert uploaded.url is not None

    # Clean up
    client.delete_object(object_key)
