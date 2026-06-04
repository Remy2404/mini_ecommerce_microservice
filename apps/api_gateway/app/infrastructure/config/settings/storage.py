"""Object storage settings."""

from pydantic import Field


class StorageSettings:
    object_storage_endpoint_url: str | None = Field(
        None,
        validation_alias="OBJECT_STORAGE_ENDPOINT_URL",
    )
    object_storage_access_key_id: str | None = Field(
        None,
        validation_alias="OBJECT_STORAGE_ACCESS_KEY_ID",
    )
    object_storage_secret_access_key: str | None = Field(
        None,
        validation_alias="OBJECT_STORAGE_SECRET_ACCESS_KEY",
    )
    object_storage_region: str = Field("us-east-1", validation_alias="OBJECT_STORAGE_REGION")
    object_storage_bucket_name: str = Field(
        "mini-ecommerce-media",
        validation_alias="OBJECT_STORAGE_BUCKET_NAME",
    )
    object_storage_public_base_url: str | None = Field(
        None,
        validation_alias="OBJECT_STORAGE_PUBLIC_BASE_URL",
    )
    object_storage_presigned_url_expire_seconds: int = Field(
        900,
        validation_alias="OBJECT_STORAGE_PRESIGNED_URL_EXPIRE_SECONDS",
    )
    object_storage_upload_max_bytes: int = Field(
        5 * 1024 * 1024,
        validation_alias="OBJECT_STORAGE_UPLOAD_MAX_BYTES",
    )

    thumbnail_max_width: int = Field(300, validation_alias="THUMBNAIL_MAX_WIDTH")
    thumbnail_max_height: int = Field(300, validation_alias="THUMBNAIL_MAX_HEIGHT")
    thumbnail_quality: int = Field(85, validation_alias="THUMBNAIL_QUALITY")
