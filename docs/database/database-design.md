# Database Design

Product, Order, and Payment services use PostgreSQL databases through
`packages.database.session`. Cart state remains in Valkey because it is a short
lived cache-style aggregate.

## Ownership

- Product Service owns product rows in `products_db`.
- Order Service owns order and order item rows in `orders_db`.
- Payment Service owns payment rows in `payments_db`.
- Cart Service owns cart keys in Valkey.

All SQL access stays inside service infrastructure repositories and uses
SQLAlchemy parameter binding.
