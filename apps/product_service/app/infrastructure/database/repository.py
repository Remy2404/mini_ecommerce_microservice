from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from apps.product_service.app.domain.entities import CategoryEntity, ProductEntity
from apps.product_service.app.infrastructure.config.settings import settings
from apps.product_service.app.infrastructure.database.session import session_scope
from apps.product_service.app.infrastructure.database.models import Category, Product
from apps.product_service.app.schemas import CategoryResponse, ProductResponse
from apps.product_service.app.infrastructure.storage.object_storage import (
    build_public_url,
)


def _product_response(product: Product) -> ProductResponse:
    return ProductResponse(
        product_id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        stock_quantity=product.stock_quantity,
        category=product.category.name,
        image_url=build_public_url(product.image_object_key) if product.image_object_key else None,
    )


def _category_response(category: Category) -> CategoryResponse:
    return CategoryResponse(
        category_id=category.id,
        name=category.name,
        description=category.description,
    )


def _product_entity(product: Product) -> ProductEntity:
    return ProductEntity(
        product_id=product.id,
        name=product.name,
        price=product.price,
        stock_quantity=product.stock_quantity,
        category=product.category.name,
        image_object_key=product.image_object_key,
    )


def _category_entity(category: Category) -> CategoryEntity:
    return CategoryEntity(
        category_id=category.id,
        name=category.name,
        description=category.description,
    )


async def create_category(
    *,
    name: str,
    description: str | None,
) -> CategoryEntity:
    async with session_scope(settings.products_database_url) as session:
        existing = await _get_category_by_name(session, name)
        if existing is not None:
            return _category_entity(existing)

        category = Category(id=uuid4(), name=name, description=description)
        session.add(category)
        await session.flush()
        return _category_entity(category)


async def save_product(product: ProductEntity) -> None:
    async with session_scope(settings.products_database_url) as session:
        category = await _get_category_by_name(session, product.category)
        if category is None:
            category = Category(id=uuid4(), name=product.category)
            session.add(category)
            await session.flush()

        existing = await session.get(Product, product.product_id.value)
        if existing is None:
            session.add(
                Product(
                    id=product.product_id.value,
                    category_id=category.id,
                    name=product.name,
                    description=product.description,
                    price=product.price.amount,
                    stock_quantity=product.stock_quantity,
                    image_object_key=product.image_object_key,
                )
            )
            return

        existing.category_id = category.id
        existing.name = product.name
        existing.description = product.description
        existing.price = product.price.amount
        existing.stock_quantity = product.stock_quantity
        existing.image_object_key = product.image_object_key


async def get_product(product_id: UUID) -> ProductEntity | None:
    async with session_scope(settings.products_database_url) as session:
        result = await session.execute(
            select(Product)
            .options(selectinload(Product.category))
            .where(Product.id == product_id, Product.is_active.is_(True))
        )
        product = result.scalar_one_or_none()

    return _product_entity(product) if product else None


async def list_products() -> list[ProductEntity]:
    async with session_scope(settings.products_database_url) as session:
        result = await session.execute(
            select(Product)
            .options(selectinload(Product.category))
            .where(Product.is_active.is_(True))
            .order_by(Product.created_at.desc(), Product.id.desc())
        )
        products = result.scalars().all()

    return [_product_entity(product) for product in products]


async def list_categories() -> list[CategoryEntity]:
    async with session_scope(settings.products_database_url) as session:
        result = await session.execute(
            select(Category).where(Category.is_active.is_(True)).order_by(Category.name)
        )
        categories = result.scalars().all()

    return [_category_entity(category) for category in categories]


async def _get_category_by_name(session, name: str) -> Category | None:
    result = await session.execute(select(Category).where(Category.name == name))
    return result.scalar_one_or_none()


async def update_product_image(product_id: UUID, new_object_key: str) -> str | None:
    """Set the product.image_object_key to new_object_key and return the
    previous object key (if any).
    """
    async with session_scope(settings.products_database_url) as session:
        product = await session.get(Product, product_id)
        if product is None:
            return None

        old_key = product.image_object_key
        product.image_object_key = new_object_key
        await session.flush()

    return old_key

