from packages.observability.metrics import order_created_total


def test_order_created_metric_can_increment():
    order_created_total.labels(service_name="test-service").inc()

    assert order_created_total is not None
