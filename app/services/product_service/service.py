from uuid import UUID, uuid4

from app.services.product_service.repository import get_product, list_products, save_product
from app.services.product_service.schemas import CreateProductRequest, ProductResponse


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

    return product


async def find_product(product_id: UUID) -> ProductResponse | None:
    return await get_product(product_id)


async def find_products() -> list[ProductResponse]:
    return await list_products()
