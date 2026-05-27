# Testing

Run all tests:

```powershell
uv run pytest
```

Coverage focus:

- Shared package config, contracts, messaging, metrics, and security helpers.
- Auth registration/login/password hashing/JWT flow.
- Product categories and product route contracts.
- Cart trusted-pricing behavior and rejection of client `unit_price`.
- Order creation, payment result consumer, status updates, and cart clearing.
- Payment fake provider, persistence contract, and idempotency lock path.
- Gateway proxy routing, auth validation, rate limiting, metrics, and safe errors.

Tests are intentionally unit-heavy so the template remains fast to validate.
Manual smoke checks should inspect existing ports and RabbitMQ consumers before
starting any local processes.
