import json
from pathlib import Path


def test_rabbitmq_definitions_include_retry_and_dlq_topology() -> None:
    definitions = json.loads(Path("infra/rabbitmq/definitions.json").read_text())

    exchange_names = {exchange["name"] for exchange in definitions["exchanges"]}
    queue_names = {queue["name"] for queue in definitions["queues"]}
    binding_keys = {binding["routing_key"] for binding in definitions["bindings"]}

    assert "ecommerce.retry.exchange" in exchange_names
    assert "ecommerce.dlx" in exchange_names
    assert "order.created.retry.queue" in queue_names
    assert "payment.succeeded.retry.queue" in queue_names
    assert "payment.failed.retry.queue" in queue_names
    assert "ecommerce.dead-letter.queue" in queue_names
    assert "order.created.retry.v1" in binding_keys
    assert "payment.succeeded.retry.v1" in binding_keys
    assert "payment.failed.retry.v1" in binding_keys
