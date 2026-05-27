# Database Design

## auth_db

- `users`
- `user_profiles`
- `user_addresses`
- `roles`
- `user_roles`

## products_db

- `categories`
- `products`

`products.category_id` references `categories.id`. Product API responses keep a
stable `category` name for clients.

## orders_db

- `orders`
- `order_items`

Orders are created from the trusted Valkey cart snapshot and start as `PENDING`.
Payment results update status to `CONFIRMED` or `CANCELLED`.

## payments_db

- `payments`

Payment rows record fake provider outcomes. Sensitive payment data is never
cached.

## Valkey

- Cart: `cart:{user_id}`
- Product read cache: `product:{product_id}`
- Gateway rate limit: `gateway:rl:{subject}`
- Payment idempotency lock: `payment:idempotency:{event_id}`
