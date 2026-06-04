"""Product image routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from apps.product_service.app.api import routes as routes_module
from apps.product_service.app.infrastructure.observability.logging import get_logger
from apps.product_service.app.infrastructure.security.acl import (
    require_product_image_write_scope,
)
from apps.product_service.app.schemas import ApiResponse

router = APIRouter()
logger = get_logger(__name__)


@router.put("/products/{product_id}/image", status_code=status.HTTP_200_OK)
async def upload_product_image_endpoint(
    product_id: UUID,
    file: UploadFile = File(...),
    _auth: None = Depends(require_product_image_write_scope),
) -> ApiResponse[dict]:
    data = await file.read()

    try:
        image_url = await routes_module.upload_product_image(product_id=product_id, data=data)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to upload product image", product_id=str(product_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image upload failed",
        )

    return ApiResponse(success=True, message="Image uploaded", data={"image_url": image_url})
