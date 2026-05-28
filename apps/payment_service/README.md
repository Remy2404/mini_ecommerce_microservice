# Payment Service

Owns `payments` in `payments_db`.

The worker consumes `order.created.v1`, acquires a Valkey idempotency lock using
`payment:idempotency:{event_id}`, simulates a provider decision, persists the
payment attempt, and publishes `payment.succeeded.v1` or `payment.failed.v1`.
No payment card data or sensitive provider payloads are cached.
