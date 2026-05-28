# Service Workflow

1. User registers through Auth Service and logs in for a JWT.
2. Product Service creates categories and products in `products_db`.
3. Cart Service receives only `user_id`, `product_id`, and `quantity`, fetches trusted product data from Product Service, and stores the cart in Valkey.
4. Order Service reads the Valkey cart snapshot, persists order rows, and publishes `order.created.v1`.
5. Payment Service consumes the order event, persists a fake payment result, and publishes `payment.succeeded.v1` or `payment.failed.v1`.
6. Order Service consumes the payment result. Success confirms the order and clears the Valkey cart; failure cancels the order and keeps the cart.
7. API Gateway routes external traffic, validates bearer tokens when enabled, rate limits through Valkey, and exposes `/health` and `/metrics`.
