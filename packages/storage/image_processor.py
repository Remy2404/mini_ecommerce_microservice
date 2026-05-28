"""Small image-upload helpers for object-storage workflows."""

from dataclasses import dataclass
from uuid import uuid4


SUPPORTED_IMAGE_CONTENT_TYPES: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class ImageValidationError(ValueError):
    """Raised when an uploaded image does not meet storage constraints."""


@dataclass(frozen=True)
class ImageUpload:
    """Validated image upload metadata."""

    object_key: str
    content_type: str
    size_bytes: int


def build_image_object_key(prefix: str, content_type: str) -> str:
    """Create a stable object key with an extension from the content type."""
    extension = SUPPORTED_IMAGE_CONTENT_TYPES.get(content_type)
    if extension is None:
        raise ImageValidationError(f"Unsupported image content type: {content_type}")

    safe_prefix = prefix.strip("/").replace("\\", "/") or "images"
    return f"{safe_prefix}/{uuid4().hex}{extension}"


def validate_image_upload(
    *,
    content_type: str,
    size_bytes: int,
    prefix: str = "products",
    max_size_bytes: int = 5 * 1024 * 1024,
) -> ImageUpload:
    """Validate image metadata and return the object-storage target."""
    if size_bytes <= 0:
        raise ImageValidationError("Image upload is empty.")
    if size_bytes > max_size_bytes:
        raise ImageValidationError("Image upload exceeds the maximum size.")

    return ImageUpload(
        object_key=build_image_object_key(prefix, content_type),
        content_type=content_type,
        size_bytes=size_bytes,
    )
