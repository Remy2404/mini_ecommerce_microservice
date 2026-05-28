# API Gateway

Provides explicit `/api/v1/*` routes for auth, categories, products, cart,
orders, and payments. It adds request IDs, validates bearer tokens when enabled,
applies Valkey-backed rate limiting, and maps downstream errors to safe
responses.

The public login flow is `POST /api/v1/auth/login`, tagged `WSO2 Gateway`, and
it authenticates directly against WSO2 Identity Server. The legacy internal
`/internal/wso2/login` route is hidden from Swagger.
