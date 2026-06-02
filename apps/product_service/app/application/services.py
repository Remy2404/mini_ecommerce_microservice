from uuid import UUID, uuid4

from apps.product_service.app.infrastructure.cache.product_cache import (
    get_product_cache,
    set_product_cache,
)
from apps.product_service.app.infrastructure.database import repository
from apps.product_service.app.schemas import (
    CategoryResponse,
    CreateCategoryRequest,
    CreateProductRequest,
    ProductResponse,
)
from packages.storage import image_processor, object_storage
from apps.product_service.app.infrastructure.cache.product_cache import (
    delete_product_cache,
)


async def create_category_for_catalog(
    request: CreateCategoryRequest,
) -> CategoryResponse:
    return await repository.create_category(name=request.name, description=request.description)


async def create_product(request: CreateProductRequest) -> ProductResponse:
    product = ProductResponse(
        product_id=uuid4(),
        name=request.name,
        description=request.description,
        price=request.price,
        stock_quantity=request.stock_quantity,
        category=request.category,
    )

    await repository.save_product(product)
    set_product_cache(product)

    return product


async def find_product(product_id: UUID) -> ProductResponse | None:
    cached_product = get_product_cache(product_id)
    if cached_product is not None:
        return cached_product

    product = await repository.get_product(product_id)
    if product is not None:
        set_product_cache(product)

    return product


async def find_products() -> list[ProductResponse]:
    return await repository.list_products()


async def find_categories() -> list[CategoryResponse]:
    return await repository.list_categories()


async def upload_product_image(*, product_id: UUID, data: bytes):
    """Process bytes, upload optimized WEBP to object storage, update DB and
    perform safe cleanup. Returns public image_url on success.
    """
  

    storage = object_storage.get_object_storage_client()

    # Process image bytes -> optimized WEBP buffer
    processed_buf, content_type = image_processor.process_image_bytes(data)

    # Build object key for webp
    object_key = image_processor.build_image_object_key("products", content_type)

    # Upload to storage
    uploaded = storage.upload_fileobj(processed_buf, object_key, content_type)

    # Persist new key in DB, capture previous key for cleanup
    try:
        old_key = await repository.update_product_image(product_id, uploaded.object_key)
    except Exception:
        # DB update failed — rollback by deleting newly uploaded object
        try:
            storage.delete_object(uploaded.object_key)
        except Exception:
            # best-effort: log later by caller
            pass
        raise

    # Invalidate cache for this product
    try:
        delete_product_cache(product_id)
    except Exception:
        # non-fatal
        pass

    # Remove old object after successful DB update
    if old_key:
        try:
            storage.delete_object(old_key)
        except Exception:
            # best-effort cleanup
            pass

    # Build public URL and return
    return storage.build_public_url(uploaded.object_key)
