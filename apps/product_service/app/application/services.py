from uuid import UUID, uuid4

from apps.product_service.app.infrastructure.cache.product_cache import (
    get_product_cache,
    set_product_cache,
)
from apps.product_service.app.infrastructure.database.repository import (
    create_category,
    get_product,
    list_categories,
    list_products,
    save_product,
)
from apps.product_service.app.schemas import (
    CategoryResponse,
    CreateCategoryRequest,
    CreateProductRequest,
    ProductResponse,
)


async def create_category_for_catalog(request: CreateCategoryRequest) -> CategoryResponse:
    return await create_category(name=request.name, description=request.description)


async def create_product(request: CreateProductRequest) -> ProductResponse:
    product = ProductResponse(
        product_id=uuid4(),
        name=request.name,
        description=request.description,
        price=request.price,
        stock_quantity=request.stock_quantity,
        category=request.category,
    )

    await save_product(product)
    set_product_cache(product)

    return product


async def find_product(product_id: UUID) -> ProductResponse | None:
    cached_product = get_product_cache(product_id)
    if cached_product is not None:
        return cached_product

    product = await get_product(product_id)
    if product is not None:
        set_product_cache(product)

    return product


async def find_products() -> list[ProductResponse]:
    return await list_products()


async def find_categories() -> list[CategoryResponse]:
    return await list_categories()
