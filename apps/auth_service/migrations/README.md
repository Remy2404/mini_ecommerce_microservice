# Auth Service Migrations

The Auth Service owns `auth_db` and manages user, profile, address, and role
tables. Run migrations from the repository root:

```powershell
uv run alembic -c apps/auth_service/alembic.ini upgrade head
uv run alembic -c apps/auth_service/alembic.ini downgrade base
```

Do not point this migration environment at any other service database.
