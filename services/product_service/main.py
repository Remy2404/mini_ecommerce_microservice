from uuid import UUID

from fastapi import FastAPI, status, HTTPException

from packages.config.settings import settings
from packages.contracts.schemas import ApiResponse
from packages.observability.logging import get_logger, setup_logging
from packages.observability.tracing import add_span_attributes, setup_tracing
from services.product_service.schemas import CreateProductRequest, ProductResponse
from prometheus_client import make_asgi_app
from packages.observability.http_metrics import HTTPMetricsMiddleware
from services.product_service.service import create_product, find_product, find_products

app = FastAPI(
    title="Product Service",
)

setup_logging(settings.product_service_name)
setup_tracing(settings.product_service_name, app)

app.mount("/metrics", make_asgi_app())
app.add_middleware(HTTPMetricsMiddleware, service_name=settings.product_service_name)

logger = get_logger(__name__)



@app.get("/health")
async def health() -> dict[str, str]:
    logger.info("Health check requested")

    return {
        "status": "ok",
        "service": settings.product_service_name,
    }


@app.post(
    "/products",
    status_code=status.HTTP_201_CREATED,
)
async def create_product_endpoint(
    request: CreateProductRequest,
) -> ApiResponse[ProductResponse]:
    product = create_product(request)

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


@app.get("/products")
async def list_products_endpoint() -> ApiResponse[list[ProductResponse]]:
    products = find_products()

    logger.info(
        "Products fetched",
        total=len(products),
    )

    return ApiResponse[list[ProductResponse]](
        success=True,
        message="Products fetched successfully",
        data=products,
    )


@app.get("/products/{product_id}")
async def get_product_endpoint(
    product_id: UUID,
) -> ApiResponse[ProductResponse]:
    product = find_product(product_id)

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
