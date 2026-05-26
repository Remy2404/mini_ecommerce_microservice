from packages.observability.metrics import order_created_total


def test_order_created_metric_can_increment():
    initial_val = order_created_total.labels(service_name="test-service")._value.get()
    order_created_total.labels(service_name="test-service").inc()
    final_val = order_created_total.labels(service_name="test-service")._value.get()

    assert final_val == initial_val + 1.0
