from uuid import UUID

from sqlalchemy import text

from packages.config.settings import settings
from packages.database.session import connect, transaction
from apps.product_service.app.schemas import ProductResponse


PRODUCT_COLUMNS = """
    id,
    name,
    description,
    price,
    stock_quantity,
    category
"""


def _product_from_row(row) -> ProductResponse:
    data = row._mapping
    return ProductResponse(
        product_id=data["id"],
        name=data["name"],
        description=data["description"],
        price=data["price"],
        stock_quantity=data["stock_quantity"],
        category=data["category"],
    )


async def save_product(product: ProductResponse) -> None:
    async with transaction(settings.products_database_url) as connection:
        await connection.execute(
            text(
                """
                INSERT INTO products (
                    id,
                    name,
                    description,
                    price,
                    stock_quantity,
                    category
                )
                VALUES (
                    :id,
                    :name,
                    :description,
                    :price,
                    :stock_quantity,
                    :category
                )
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    price = EXCLUDED.price,
                    stock_quantity = EXCLUDED.stock_quantity,
                    category = EXCLUDED.category,
                    updated_at = CURRENT_TIMESTAMP
                """
            ),
            {
                "id": product.product_id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "stock_quantity": product.stock_quantity,
                "category": product.category,
            },
        )


async def get_product(product_id: UUID) -> ProductResponse | None:
    async with connect(settings.products_database_url) as connection:
        result = await connection.execute(
            text(
                f"""
                SELECT {PRODUCT_COLUMNS}
                FROM products
                WHERE id = :product_id
                  AND is_active = TRUE
                """
            ),
            {"product_id": product_id},
        )
        row = result.first()

    if row is None:
        return None

    return _product_from_row(row)


async def list_products() -> list[ProductResponse]:
    async with connect(settings.products_database_url) as connection:
        result = await connection.execute(
            text(
                f"""
                SELECT {PRODUCT_COLUMNS}
                FROM products
                WHERE is_active = TRUE
                ORDER BY created_at DESC, id DESC
                """
            )
        )
        rows = result.all()

    return [_product_from_row(row) for row in rows]
