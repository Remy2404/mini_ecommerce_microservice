# Saga Flow

The order-payment saga is asynchronous and RabbitMQ-backed.

1. Order Service validates cart state and persists a pending order.
2. Order Service publishes `order.created`.
3. Payment Service consumes `order.created`, persists the payment attempt, and
   publishes either `payment.success` or `payment.failed`.
4. Order Service consumes the payment result and updates the order status to
   `CONFIRMED` or `CANCELLED`.
5. On payment success, Order Service clears the user's cart key from Valkey.

Event DTOs live in `libs/ecommerce-contracts/ecommerce_contracts/order` and
`libs/ecommerce-contracts/ecommerce_contracts/payment`. RabbitMQ setup lives in
`libs/ecommerce-messaging/ecommerce_messaging`.
