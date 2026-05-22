# Security

## API Gateway Authentication

The API Gateway can run in two modes:

- Local development: `GATEWAY_AUTH_ENABLED=false` bypasses JWT validation and returns a local demo principal.
- Protected mode: `GATEWAY_AUTH_ENABLED=true` requires a Bearer token. JWT bearer tokens are validated against WSO2 Identity Server JWKS, issuer, audience, and algorithm settings. Opaque WSO2 access tokens are validated through the WSO2 introspection endpoint.

Production deployments must enable gateway auth and validate WSO2 TLS certificates:

```env
GATEWAY_AUTH_ENABLED=true
WSO2_VERIFY_SSL=true
```

Do not log access tokens, refresh tokens, client secrets, or full authorization headers.

## WSO2 Identity Server Local Setup

Use WSO2 Identity Server as the local OpenID Connect issuer for Phase 6 gateway authentication.

1. Start WSO2 Identity Server:

```powershell
docker compose -f infra/docker-compose.yml --profile identity up -d wso2
```

2. Open the WSO2 Console:

```text
https://localhost:9443/console
```

3. Sign in with the default local credentials:

```text
admin / admin
```

4. Create an application:

```text
Application name: mini-ecommerce-api
Protocol: OAuth2 / OIDC
```

5. Enable these grant types for local testing:

```text
Authorization Code
Client Credentials
Refresh Token
Password
```

6. Configure local callback and origins:

```text
Callback URL: http://localhost:8000/auth/callback
Allowed origins:
  http://localhost:8000
  http://localhost:8001
  http://localhost:8002
  http://localhost:8003
```

7. Configure the API audience and endpoints:

```text
API audience: mini-ecommerce-api
JWKS endpoint: https://localhost:9443/oauth2/jwks
Token endpoint: https://localhost:9443/oauth2/token
Introspection endpoint: https://localhost:9443/oauth2/introspect
Userinfo endpoint: https://localhost:9443/oauth2/userinfo
```

8. Copy the generated client ID and client secret into your local `.env`.

9. Configure these gateway values:

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
JWT_ALGORITHM=RS256
```

Local WSO2 installs normally use a self-signed certificate. Keep `WSO2_VERIFY_SSL=false` only for local development unless you import the local WSO2 CA certificate into the trust store used by Python/httpx. In production, use a certificate issued by a trusted CA and set `WSO2_VERIFY_SSL=true`.

When auth is enabled, a request without a Bearer token must return `401`. A malformed, expired, inactive, wrong-audience, or wrong-issuer token must also return `401`. Use the `access_token` from `/auth/login` for gateway requests, not the `id_token`.
