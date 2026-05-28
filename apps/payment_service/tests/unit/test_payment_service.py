from decimal import Decimal

from fastapi.testclient import TestClient

from apps.payment_service.app.application.services import process_fake_payment
from apps.payment_service.app.infrastructure.database.models import Payment
from apps.payment_service.app.main import app
from packages.config.settings import settings


def test_fake_payment_provider_success_and_failure(monkeypatch) -> None:
    monkeypatch.setattr(settings, "payment_success_rate", 0.5)

    assert process_fake_payment(amount=Decimal("10.00"), random_value=0.1).succeeded
    failed = process_fake_payment(amount=Decimal("10.00"), random_value=0.9)
    assert not failed.succeeded
    assert failed.failure_reason == "Simulated payment failure"


def test_payment_model_maps_payments_table() -> None:
    assert Payment.__tablename__ == "payments"
    assert "order_id" in Payment.__table__.columns
    assert "correlation_id" in Payment.__table__.columns


def test_payment_health_endpoint_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": settings.payment_service_name}
