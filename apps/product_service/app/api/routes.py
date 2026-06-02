"""Product router."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Depends, Header

from packages.config.settings import settings
from packages.contracts.common.schemas import ApiResponse
from packages.observability.logging import get_logger
from packages.observability.tracing import add_span_attributes
from apps.product_service.app.schemas import (
    CategoryResponse,
    CreateCategoryRequest,
    CreateProductRequest,
    ProductResponse,
)
from apps.product_service.app.application.services import (
    create_category_for_catalog,
    create_product,
    find_categories,
    find_product,
    find_products,
    upload_product_image,
)
from packages.errors.exceptions import to_http_exception
from packages.security.permissions import require_scope
from packages.security import jwt_validator
from packages.security.jwt_validator import TokenValidationError

router = APIRouter()

logger = get_logger(__name__)


@router.get("/health")
async def health() -> dict[str, str]:
    logger.info("Health check requested")

    return {
        "status": "ok",
        "service": settings.product_service_name,
    }


@router.post(
    "/categories",
    status_code=status.HTTP_201_CREATED,
)
async def create_category_endpoint(
    request: CreateCategoryRequest,
) -> ApiResponse[CategoryResponse]:
    category = await create_category_for_catalog(request)

    return ApiResponse[CategoryResponse](
        success=True,
        message="Category created successfully",
        data=category,
    )


@router.get("/categories")
async def list_categories_endpoint() -> ApiResponse[list[CategoryResponse]]:
    categories = await find_categories()

    return ApiResponse[list[CategoryResponse]](
        success=True,
        message="Categories fetched successfully",
        data=categories,
    )


@router.post(
    "/products",
    status_code=status.HTTP_201_CREATED,
)
async def create_product_endpoint(
    request: CreateProductRequest,
) -> ApiResponse[ProductResponse]:
    product = await create_product(request)

    add_span_attributes(
        {
            "product.id": str(product.product_id),
            "product.category": product.category,
        }
    )

    logger.info(
        "Product created",
        product_id=str(product.product_id),
        category=product.category,
    )

    return ApiResponse[ProductResponse](
        success=True,
        message="Product created successfully",
        data=product,
    )


@router.get("/products")
async def list_products_endpoint() -> ApiResponse[list[ProductResponse]]:
    products = await find_products()

    logger.info(
        "Products fetched",
        total=len(products),
    )

    return ApiResponse[list[ProductResponse]](
        success=True,
        message="Products fetched successfully",
        data=products,
    )


@router.get("/products/{product_id}")
async def get_product_endpoint(
    product_id: UUID,
) -> ApiResponse[ProductResponse]:
    product = await find_product(product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return ApiResponse[ProductResponse](
        success=True,
        message="Product fetched successfully",
        data=product,
    )


async def _require_product_image_write_scope(
    authorization: str | None = Header(None),
) -> None:
    """Validate the Authorization header against WSO2 and require upload scope.

    The API gateway forwards the original Authorization header; downstream
    services should validate the token and enforce the WSO2 API scope.
    """
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization")

    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header")

    token = authorization.split(None, 1)[1]
    try:
        payload = await jwt_validator.validate_wso2_access_token(token)
    except TokenValidationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    except Exception as exc:
        # Treat provider errors as 503
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Auth provider unavailable") from exc

    try:
        require_scope(payload.get("scope", ""), "product_image_write")
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.put("/products/{product_id}/image", status_code=status.HTTP_200_OK)
async def upload_product_image_endpoint(
    product_id: UUID,
    file: UploadFile = File(...),
    _auth: None = Depends(_require_product_image_write_scope),
) -> ApiResponse[dict]:
    # Read bytes
    data = await file.read()

    try:
        image_url = await upload_product_image(product_id=product_id, data=data)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to upload product image", product_id=str(product_id))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Image upload failed")

    return ApiResponse(success=True, message="Image uploaded", data={"image_url": image_url})
