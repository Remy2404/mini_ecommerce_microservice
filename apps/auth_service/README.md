# Auth Service

Uses WSO2 Identity Server as the source of truth for user identity.

## Routes

- `POST /auth/register`
- `POST /internal/wso2/login` (hidden from Swagger; used for WSO2 password-grant login)
- `GET /auth/users`
- `GET /auth/users/search`
- `GET /auth/users/{user_id}`

Access tokens are issued by WSO2 through the API Gateway `/api/v1/auth/login`
route. Local auth database models are reserved for app-owned metadata, not WSO2
identity ownership.
