import re
from pathlib import Path


def test_compose_defines_healthchecks_for_runtime_dependencies() -> None:
    compose = Path("infra/docker-compose.yml").read_text()

    for service_name in (
        "rabbitmq",
        "valkey",
        "postgres-primary",
        "auth-service",
        "product-service",
        "cart-service",
        "order-service",
        "payment-service",
        "api-gateway",
    ):
        service_marker = f"  {service_name}:"
        service_start = compose.index(service_marker)
        next_match = re.search(
            r"\n  [a-zA-Z0-9_-]+:\n",
            compose[service_start + len(service_marker) :],
        )
        next_service = (
            service_start + len(service_marker) + next_match.start()
            if next_match
            else -1
        )
        service_block = compose[
            service_start : next_service if next_service > 0 else None
        ]

        assert "healthcheck:" in service_block


def test_compose_uses_healthy_dependency_conditions_for_service_startup() -> None:
    compose = Path("infra/docker-compose.yml").read_text()

    assert "condition: service_healthy" in compose
    assert "postgres-primary:\n        condition: service_healthy" in compose
    assert "rabbitmq:\n        condition: service_healthy" in compose
    assert "valkey:\n        condition: service_healthy" in compose
