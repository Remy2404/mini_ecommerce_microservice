"""Product router."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from packages.config.settings import settings
from packages.contracts.schemas import ApiResponse
from packages.observability.logging import get_logger
from packages.observability.tracing import add_span_attributes
from services.product_service.schemas import CreateProductRequest, ProductResponse
from services.product_service import main as product_main

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
	"/products",
	status_code=status.HTTP_201_CREATED,
)
async def create_product_endpoint(
	request: CreateProductRequest,
) -> ApiResponse[ProductResponse]:
	product = product_main.create_product(request)

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
	products = product_main.find_products()

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
	product = product_main.find_product(product_id)

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
