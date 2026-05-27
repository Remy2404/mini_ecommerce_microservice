"""Object storage helpers for reusable service templates."""

from packages.storage.image_processor import (
    ImageUpload,
    ImageValidationError,
    build_image_object_key,
    validate_image_upload,
)
from packages.storage.object_storage import (
    ObjectStorageClient,
    ObjectStorageError,
    UploadedObject,
    get_object_storage_client,
)

__all__ = [
    "ImageUpload",
    "ImageValidationError",
    "ObjectStorageClient",
    "ObjectStorageError",
    "UploadedObject",
    "build_image_object_key",
    "get_object_storage_client",
    "validate_image_upload",
]
