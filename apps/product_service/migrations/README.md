# Product Service Migrations

The Product Service owns `products_db` and manages category and product tables.
Run migrations from the repository root:

```powershell
uv run alembic -c apps/product_service/alembic.ini upgrade head
uv run alembic -c apps/product_service/alembic.ini downgrade base
```

Product catalog data must not be migrated through another service.
