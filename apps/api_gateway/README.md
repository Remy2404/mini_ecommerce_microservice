# API Gateway

Provides explicit `/api/v1/*` routes for auth, categories, products, cart,
orders, and payments. It adds request IDs, validates bearer tokens when enabled,
applies Valkey-backed rate limiting, and maps downstream errors to safe
responses.

The legacy top-level `/auth/login` route remains available for WSO2 local token
testing. Application auth routes are proxied under `/api/v1/auth/*`.
