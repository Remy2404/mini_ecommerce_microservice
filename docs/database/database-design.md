# Database Design

Auth, Product, Order, and Payment services use PostgreSQL databases through
`packages.database.session`. Cart state remains in Valkey because it is a short
lived cache-style aggregate.

## Ownership

- Auth Service uses WSO2 Identity Server as the source of truth for identity
  and user management. `auth_db` keeps only the current service-owned
  compatibility tables (`users`, `user_profiles`); legacy local identity tables
  (`roles`, `user_addresses`, `user_roles`) are removed by migration.
- Product Service owns product rows in `products_db`.
- Order Service owns order and order item rows in `orders_db`.
- Payment Service owns payment rows in `payments_db`.
- Cart Service owns cart keys in Valkey.

All SQL access stays inside service infrastructure repositories and uses
SQLAlchemy parameter binding.
