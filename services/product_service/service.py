from uuid import UUID, uuid4

from services.product_service.repository import get_product, list_products, save_product
from services.product_service.schemas import CreateProductRequest, ProductResponse


def create_product(request: CreateProductRequest) -> ProductResponse:
    product = ProductResponse(
        product_id=uuid4(),
        name=request.name,
        description=request.description,
        price=request.price,
        stock_quantity=request.stock_quantity,
        category=request.category,
    )

    save_product(product)

    return product


def find_product(product_id: UUID) -> ProductResponse | None:
    return get_product(product_id)


def find_products() -> list[ProductResponse]:
    return list_products()
