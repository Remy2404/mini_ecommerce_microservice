from http import HTTPStatus
from uuid import UUID

import httpx
from pydantic import ValidationError

from apps.cart_service.app.domain.exceptions import (
    ProductLookupRejectedError,
    ProductNotFoundError,
    ProductServiceUnavailableError,
)
from packages.config.settings import settings
from packages.contracts.common.schemas import ApiResponse, ProductResponse


def _product_url(product_id: UUID) -> str:
    return f"{settings.product_service_url.rstrip('/')}/products/{product_id}"


async def fetch_product(product_id: UUID) -> ProductResponse:
    try:
        async with httpx.AsyncClient(
            timeout=settings.gateway_request_timeout_seconds,
        ) as client:
            response = await client.get(_product_url(product_id))
    except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
        raise ProductServiceUnavailableError from exc
    except httpx.HTTPError as exc:
        raise ProductServiceUnavailableError from exc

    if response.status_code == HTTPStatus.NOT_FOUND:
        raise ProductNotFoundError

    if response.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
        raise ProductServiceUnavailableError

    if response.status_code >= HTTPStatus.BAD_REQUEST:
        raise ProductLookupRejectedError

    try:
        product_response = ApiResponse[ProductResponse].model_validate(response.json())
    except (ValueError, ValidationError) as exc:
        raise ProductServiceUnavailableError from exc

    product = product_response.data
    if (
        not product_response.success
        or product is None
        or product.product_id != product_id
    ):
        raise ProductServiceUnavailableError

    return product
