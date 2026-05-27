# Mini E-Commerce Production Template Plan

## Goal
Convert the existing mini-ecommerce backend into a complete FastAPI microservice template using `apps/*`, shared `packages/*`, async SQLAlchemy ORM, PostgreSQL database-per-service, Valkey for cart/cache/locks only, RabbitMQ saga events, and production-style observability.

## Phase 0 Findings
- Current repo already has `apps/*`, `packages/*`, infra, docs, and tests; baseline `uv run pytest` passes with `65 passed in 1.99s`.
- `auth_service` is missing.
- Current product/order/payment persistence uses raw SQL helpers, not SQLAlchemy async ORM models/repositories.
- Current schema lacks `auth_db`, `categories`, and full requested auth tables.
- Several zero-byte `__init__.py` files and docstring-only helper files violate the no-empty-placeholder rule.
- `services/` legacy root is absent; only an `apps/api_gateway/app/application/services` package exists.

## Implementation Tasks
- [ ] Phase 1: Normalize shared packages for config, async DB sessions, Valkey, RabbitMQ helpers, contracts, security, errors, logging, tracing, metrics. Verify: `uv run pytest`.
- [ ] Phase 2: Add `auth_service` with ORM models for users, profiles, addresses, roles, user roles, password hashing, JWT issue/validate, profile/address routes, and tests. Verify: `uv run pytest`.
- [ ] Phase 3: Rework `product_service` around category/product ORM models, repositories, service layer, optional Valkey read cache, category/product routes, and tests. Verify: `uv run pytest`.
- [ ] Phase 4: Harden `cart_service` Valkey cart storage and Product Service client so requests accept only `user_id`, `product_id`, `quantity`; trusted product price/name comes from Product Service. Verify: `uv run pytest`.
- [ ] Phase 5: Rework `order_service` ORM models, repositories, create-order use case, order.created publisher, payment-result consumer, success-only cart clearing, and tests. Verify: `uv run pytest`.
- [ ] Phase 6: Rework `payment_service` ORM persistence, fake provider, Valkey idempotency lock, order.created consumer, payment result publishing, and tests. Verify: `uv run pytest`.
- [ ] Phase 7: Rebuild `api_gateway` explicit routes for auth/products/categories/cart/orders/payments, JWT validation, request ID, rate limit, safe proxy/error mapping, health/metrics, Swagger routes, and tests. Verify: `uv run pytest`.
- [ ] Phase 8: Update infra and docs: Docker Compose, DB init scripts for all four service DBs, Valkey config, RabbitMQ definitions, Prometheus, Grafana, README, and production docs. Verify: `uv run pytest`.
- [ ] Phase 9: Add end-to-end tests for auth, product, cart, order, payment success/failure saga, cart clear/keep rules, gateway route flow, metrics, and protected routes. Verify: `uv run pytest`.

## Execution Rules
- Stop immediately and report if any phase test run fails.
- Do not start duplicate local services or consumers during smoke checks; inspect current runtime state first and reuse healthy processes.
- Do not hardcode secrets; all service config flows through `packages/config/settings.py`.
- Keep route handlers thin, business logic in `application`, persistence/external systems in `infrastructure`, and DTOs in `schemas`.
- Remove or fill empty placeholder files with meaningful exports/docstrings only when the package needs to exist.

## Assumption To Confirm
The requested table list and relationships override the current incomplete `docs/database/database-design.md` and `infra/postgres/init-databases.sql`; implementation will update those files to match the requested production template.
