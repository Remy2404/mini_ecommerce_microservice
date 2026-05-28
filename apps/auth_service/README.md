# Auth Service

Owns users, profiles, addresses, roles, and user-role assignments in `auth_db`.

## Routes

- `POST /auth/register`
- `POST /internal/wso2/login` (hidden from Swagger; used for WSO2 password-grant login)
- `GET /auth/me`
- `POST /auth/addresses`
- `GET /auth/addresses`
- `DELETE /auth/addresses/{address_id}`
- `POST /auth/roles`
- `POST /auth/users/{user_id}/roles`
- `GET /auth/users/{user_id}/roles`

Passwords are stored as PBKDF2 hashes. Access tokens are issued by WSO2
through the API Gateway `/api/v1/auth/login` route.
