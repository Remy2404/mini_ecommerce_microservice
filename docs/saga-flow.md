# Saga Flow

RabbitMQ exchange: `ecommerce.exchange`.

Events:

- `order.created.v1`
- `payment.succeeded.v1`
- `payment.failed.v1`

Flow:

1. `order_service` persists a `PENDING` order and its `order_items`.
2. `order_service` publishes `order.created.v1` to `order.created.queue`.
3. `payment_service` acquires `payment:idempotency:{event_id}` in Valkey.
4. `payment_service` persists a payment row in `payments_db`.
5. `payment_service` publishes `payment.succeeded.v1` or `payment.failed.v1`.
6. `order_service` consumes the payment result from `payment.result.queue`.
7. Success changes order status to `CONFIRMED` and clears `cart:{user_id}`.
8. Failure changes order status to `CANCELLED` and leaves `cart:{user_id}` intact.
