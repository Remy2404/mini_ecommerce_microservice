"""Product router."""

from importlib import import_module

from fastapi import APIRouter

from apps.product_service.app.application.services import (
    create_category_for_catalog as _create_category_for_catalog,
)
from apps.product_service.app.application.services import (
    create_product as _create_product,
)
from apps.product_service.app.application.services import (
    find_categories as _find_categories,
)
from apps.product_service.app.application.services import find_product as _find_product
from apps.product_service.app.application.services import find_products as _find_products
from apps.product_service.app.application.services import (
    upload_product_image as _upload_product_image,
)

create_category_for_catalog = _create_category_for_catalog
create_product = _create_product
find_categories = _find_categories
find_product = _find_product
find_products = _find_products
upload_product_image = _upload_product_image

health_router = import_module(".health", __name__).router
categories_router = import_module(".categories", __name__).router
products_router = import_module(".products", __name__).router
images_router = import_module(".images", __name__).router

router = APIRouter()
router.include_router(health_router)
router.include_router(categories_router)
router.include_router(products_router)
router.include_router(images_router)

__all__ = [
    "create_category_for_catalog",
    "create_product",
    "find_categories",
    "find_product",
    "find_products",
    "router",
    "upload_product_image",
]
