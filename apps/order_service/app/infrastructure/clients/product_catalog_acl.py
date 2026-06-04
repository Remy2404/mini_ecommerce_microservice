from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

import httpx
from pydantic import BaseModel

from apps.order_service.app.infrastructure.config.settings import settings
from apps.order_service.app.infrastructure.errors.exceptions import (
    ConflictError,
    NotFoundError,
    ServiceUnavailableError,
)


class ProductCatalogItemResponse(BaseModel):
    product_id: UUID
    name: str
    description: str | None = None
    price: Decimal
    stock_quantity: int
    category: str
    image_url: str | None = None


class ProductCatalogEnvelope(BaseModel):
    success: bool
    message: str
    data: ProductCatalogItemResponse | None = None


@dataclass(frozen=True, slots=True)
class ProductCatalogQuote:
    product_id: UUID
    product_name: str
    unit_price: Decimal
    stock_quantity: int
    currency: str = "USD"


@dataclass(frozen=True, slots=True)
class ProductQuoteLine:
    product_id: UUID
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


async def get_product_quote(product_id: UUID) -> ProductCatalogQuote:
    try:
        async with httpx.AsyncClient(
            base_url=settings.product_service_url,
            timeout=5.0,
        ) as client:
            response = await client.get(f"/products/{product_id}")
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError("Product not found", product_id=str(product_id)) from exc
        raise ServiceUnavailableError(
            "Product catalog request failed",
            product_id=str(product_id),
            status_code=exc.response.status_code,
        ) from exc
    except httpx.HTTPError as exc:
        raise ServiceUnavailableError(
            "Product catalog unavailable",
            product_id=str(product_id),
        ) from exc

    envelope = ProductCatalogEnvelope.model_validate(response.json())
    if not envelope.success or envelope.data is None:
        raise ServiceUnavailableError(
            "Product catalog returned an invalid response",
            product_id=str(product_id),
        )

    if envelope.data.stock_quantity <= 0:
        raise ConflictError(
            "Product is out of stock",
            product_id=str(product_id),
            stock_quantity=envelope.data.stock_quantity,
        )

    return ProductCatalogQuote(
        product_id=envelope.data.product_id,
        product_name=envelope.data.name,
        unit_price=envelope.data.price,
        stock_quantity=envelope.data.stock_quantity,
    )
