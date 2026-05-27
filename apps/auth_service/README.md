# Auth Service

Owns users, profiles, addresses, roles, and user-role assignments in `auth_db`.

## Routes

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `POST /auth/addresses`
- `GET /auth/addresses`
- `DELETE /auth/addresses/{address_id}`
- `POST /auth/roles`
- `POST /auth/users/{user_id}/roles`
- `GET /auth/users/{user_id}/roles`

Passwords are stored as PBKDF2 hashes. JWT signing uses `JWT_SECRET_KEY` from
the environment and refuses to issue local JWTs if that secret is missing.
