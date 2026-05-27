from apps.order_service.app.infrastructure.database.models import Order, OrderItem


def test_order_models_map_required_tables() -> None:
    assert Order.__tablename__ == "orders"
    assert OrderItem.__tablename__ == "order_items"
    assert "user_id" in Order.__table__.columns
    assert "order_id" in OrderItem.__table__.columns
