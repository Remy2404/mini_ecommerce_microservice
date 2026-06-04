"""Category routes."""

from fastapi import APIRouter, status

from apps.product_service.app.api import routes as routes_module
from apps.product_service.app.schemas import ApiResponse, CategoryResponse, CreateCategoryRequest

router = APIRouter()


@router.post("/categories", status_code=status.HTTP_201_CREATED)
async def create_category_endpoint(
    request: CreateCategoryRequest,
) -> ApiResponse[CategoryResponse]:
    category = await routes_module.create_category_for_catalog(request)

    return ApiResponse[CategoryResponse](
        success=True,
        message="Category created successfully",
        data=category,
    )


@router.get("/categories")
async def list_categories_endpoint() -> ApiResponse[list[CategoryResponse]]:
    categories = await routes_module.find_categories()

    return ApiResponse[list[CategoryResponse]](
        success=True,
        message="Categories fetched successfully",
        data=categories,
    )
