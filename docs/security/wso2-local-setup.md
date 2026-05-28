# WSO2 Local Setup

## Purpose

This guide configures WSO2 Identity Server as the local OpenID Connect issuer for the API Gateway. It does not require a live WSO2 server for unit tests, but the gateway needs WSO2 running when `GATEWAY_AUTH_ENABLED=true`.

## Prerequisites

- WSO2 Identity Server running locally.
- API Gateway `.env` copied from `.env.example`.
- No real production secrets in local docs, examples, or commits.

## Start WSO2

Start the local container from the repository root:

```powershell
docker compose -f infra/docker-compose.yml --profile identity up -d wso2
```

Then open the console:

```text
https://localhost:9443/console
```

Sign in with the default local administrator account:

```text
admin / admin
```

Local WSO2 uses HTTPS with a self-signed certificate by default. Browser and client warnings are expected unless you trust the local certificate.

## Create the OIDC Application

1. Open the WSO2 Console.
2. Create a new standard OIDC application for the API Gateway.
3. Set the application name to `mini-ecommerce-api`.
4. Select `OAuth2 / OIDC` as the protocol.
5. Enable these grant types for local testing:
   - Authorization Code
   - Client Credentials
   - Refresh Token
   - Password
6. Set the callback URL to `http://localhost:8000/auth/callback`.
7. Add these allowed origins:
   - `http://localhost:8000`
   - `http://localhost:8001`
   - `http://localhost:8002`
   - `http://localhost:8003`
8. Use `mini-ecommerce-api` as the expected API audience.
9. Save the generated client ID and client secret in your local `.env`.

Do not commit the generated client secret.

## WSO2 Endpoints

Use these local endpoints in gateway configuration and manual checks:

```text
JWKS endpoint: https://localhost:9443/oauth2/jwks
Token endpoint: https://localhost:9443/oauth2/token
Introspection endpoint: https://localhost:9443/oauth2/introspect
Userinfo endpoint: https://localhost:9443/oauth2/userinfo
```

## Gateway Environment

For local protected mode:

```env
GATEWAY_AUTH_ENABLED=true
WSO2_BASE_URL=https://localhost:9443
WSO2_ISSUER=https://localhost:9443/oauth2/token
WSO2_AUDIENCE=mini-ecommerce-api
WSO2_JWKS_URL=https://localhost:9443/oauth2/jwks
WSO2_TOKEN_URL=https://localhost:9443/oauth2/token
WSO2_INTROSPECTION_URL=https://localhost:9443/oauth2/introspect
WSO2_VERIFY_SSL=false
WSO2_REQUEST_TIMEOUT_SECONDS=10
WSO2_CLIENT_ID=replace-with-local-client-id
WSO2_CLIENT_SECRET=replace-with-local-client-secret
JWT_ALGORITHM=RS256
```

For local development without WSO2:

```env
GATEWAY_AUTH_ENABLED=false
```

## SSL Verification

`WSO2_VERIFY_SSL=false` is acceptable only for local development against the default self-signed WSO2 certificate. Use one of these production approaches instead:

- Issue WSO2 a certificate from a trusted CA.
- Import the private CA into the runtime trust store and keep verification enabled.

Production expectation:

```env
GATEWAY_AUTH_ENABLED=true
WSO2_VERIFY_SSL=true
```

## Run the Gateway

Start downstream services and the gateway:

```powershell
uv run uvicorn apps.product_service.app.main:app --reload --port 8001
uv run uvicorn apps.cart_service.app.main:app --reload --port 8002
uv run uvicorn apps.order_service.app.main:app --reload --port 8003
uv run uvicorn apps.api_gateway.app.main:app --reload --port 8000
```

## Smoke Checks

Auth disabled:

```powershell
curl.exe -i http://127.0.0.1:8000/api/v1/products
```

Auth enabled without a token should fail:

```powershell
$env:GATEWAY_AUTH_ENABLED = "true"
curl.exe -i http://127.0.0.1:8000/api/v1/products
```

Expected result: `401`.

Auth enabled with a token:

```powershell
curl.exe -i http://127.0.0.1:8000/api/v1/products -H "Authorization: Bearer <access-token>"
```

Expected result: the gateway validates opaque WSO2 access tokens through token introspection, validates JWT bearer tokens through JWKS, and proxies the request.

Use the Swagger login endpoint with the Password grant enabled in WSO2:

```powershell
curl.exe -i -X POST http://127.0.0.1:8000/auth/login `
  -H "Content-Type: application/json" `
  -d "{\"username\":\"admin\",\"password\":\"admin\",\"scope\":\"openid profile email\"}"
```

The endpoint exchanges the username and password with `https://localhost:9443/oauth2/token` using `grant_type=password`. The gateway sends configured WSO2 client credentials only to WSO2 token and introspection endpoints and does not log the username, password, token, or client secret.

Use the returned `access_token` in Swagger Authorize. Paste the raw token value; Swagger adds the `Bearer` prefix for you. Do not use the `id_token` as the API bearer token.

## Disable Auth Again for Demo

Switch the gateway back to local demo mode and restart it:

```powershell
$env:GATEWAY_AUTH_ENABLED = "false"
uv run uvicorn apps.api_gateway.app.main:app --reload --port 8000
```

## Troubleshooting

- `401 Missing bearer token`: auth is enabled and the request has no `Authorization: Bearer ...` header.
- `401 Invalid token`: token signature, issuer, audience, expiration, algorithm validation, or introspection validation failed.
- `503 Authentication service unavailable`: the gateway could not reach WSO2 JWKS or introspection.
- TLS certificate errors: keep `WSO2_VERIFY_SSL=false` only for local self-signed certificates, or trust the local WSO2 certificate.
