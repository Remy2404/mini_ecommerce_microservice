import json
from decimal import Decimal
from uuid import UUID

from packages.cache.valkey_client import get_valkey_client
from services.product_service.schemas import ProductResponse

PRODUCT_KEY_PREFIX = "product"
PRODUCT_INDEX_KEY = "products:index"


def _product_key(product_id: str) -> str:
    return f"{PRODUCT_KEY_PREFIX}:{product_id}"


def save_product(product: ProductResponse) -> None:
    client = get_valkey_client()

    payload = product.model_dump(mode="json")
    payload["price"] = str(product.price)

    client.set(
        _product_key(str(product.product_id)),
        json.dumps(payload),
    )

    client.sadd(
        PRODUCT_INDEX_KEY,
        str(product.product_id),
    )


def get_product(product_id: UUID) -> ProductResponse | None:
    client = get_valkey_client()

    raw_product = client.get(
        _product_key(str(product_id)),
    )

    if raw_product is None:
        return None

    data = json.loads(str(raw_product))
    data["price"] = Decimal(data["price"])

    return ProductResponse(**data)


def list_products() -> list[ProductResponse]:
    client = get_valkey_client()

    product_ids = client.smembers(PRODUCT_INDEX_KEY)

    products: list[ProductResponse] = []

    for product_id in product_ids:
        product = get_product(UUID(str(product_id)))

        if product is not None:
            products.append(product)

    return products
