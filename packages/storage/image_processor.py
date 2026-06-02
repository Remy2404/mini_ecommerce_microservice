"""Small image-upload helpers for object-storage workflows.

This module validates and processes uploaded bytes using Pillow and outputs
optimized WEBP bytes suitable for public catalog storage.
"""

from dataclasses import dataclass
from io import BytesIO
from typing import Tuple
from uuid import uuid4

from PIL import Image, ExifTags


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


def process_image_bytes(
    data: bytes, *, max_width: int = 1200, max_height: int = 1200
) -> Tuple[BytesIO, str]:
    """Process raw image bytes and return a BytesIO with WEBP data and the
    content type string.

    Steps:
    - Verify bytes are a supported image
    - Apply EXIF orientation if present
    - Resize to fit within max_width/max_height preserving aspect
    - Encode to optimized WEBP and return buffer
    """
    try:
        img = Image.open(BytesIO(data))
    except Exception as exc:  # Pillow raises various errors
        raise ImageValidationError("Invalid image data") from exc

    # Apply EXIF orientation if present
    try:
        exif = img._getexif()
        if exif:
            for tag, value in ExifTags.TAGS.items():
                if value == "Orientation":
                    orientation_tag = tag
                    break
            else:
                orientation_tag = None

            if orientation_tag and orientation_tag in exif:
                orientation = exif[orientation_tag]
                if orientation == 3:
                    img = img.rotate(180, expand=True)
                elif orientation == 6:
                    img = img.rotate(270, expand=True)
                elif orientation == 8:
                    img = img.rotate(90, expand=True)
    except Exception:
        # Non-fatal: EXIF parsing can fail on malformed EXIF - ignore
        pass

    # Convert to RGB if necessary
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    # Resize preserving aspect ratio
    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

    out = BytesIO()
    try:
        img.save(
            out,
            format="WEBP",
            quality=80,
            method=6,
            optimize=True,
        )
    except Exception as exc:
        raise ImageValidationError("Failed to encode image") from exc

    out.seek(0)
    return out, "image/webp"
