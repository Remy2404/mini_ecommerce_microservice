from fastapi.testclient import TestClient
from packages.config.settings import settings
from services.cart_service.main import app

def test_health_endpoint_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": settings.cart_service_name}

def test_metrics_endpoint_returns_prometheus_data() -> None:
    with TestClient(app) as client:
        # Generate some traffic first
        client.get("/health")
        
        response = client.get("/metrics")

    assert response.status_code == 200
    assert "http_request_total" in response.text
