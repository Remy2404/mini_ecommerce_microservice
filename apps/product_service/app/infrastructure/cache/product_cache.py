"""Valkey product read cache."""

from uuid import UUID

from apps.product_service.app.schemas import ProductResponse
from packages.cache.valkey_client import cache_delete, cache_get, cache_set
from packages.config.settings import settings


def _cache_key(product_id: UUID) -> str:
    return f"product:{product_id}"


def get_product_cache(product_id: UUID) -> ProductResponse | None:
    try:
        cached = cache_get(_cache_key(product_id))
    except Exception:
        return None

    if not cached:
        return None

    try:
        return ProductResponse.model_validate_json(cached)
    except ValueError:
        return None


def set_product_cache(product: ProductResponse) -> None:
    try:
        cache_set(
            _cache_key(product.product_id),
            product.model_dump_json(),
            ttl_seconds=settings.product_cache_ttl_seconds,
        )
    except Exception:
        return


def delete_product_cache(product_id: UUID) -> None:
    try:
        cache_delete(_cache_key(product_id))
    except Exception:
        return
