# Order Service

Owns `orders` and `order_items` in `orders_db`.

The service creates pending orders from the Valkey cart snapshot, publishes
`order.created.v1`, consumes payment results, updates status to `CONFIRMED` or
`CANCELLED`, and clears the cart only after successful payment.
