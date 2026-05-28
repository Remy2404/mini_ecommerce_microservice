"""Product Service request and response DTOs."""

from apps.product_service.app.schemas.requests import (
    CreateCategoryRequest,
    CreateProductRequest,
)
from apps.product_service.app.schemas.responses import CategoryResponse, ProductResponse

__all__ = [
    "CategoryResponse",
    "CreateCategoryRequest",
    "CreateProductRequest",
    "ProductResponse",
]
