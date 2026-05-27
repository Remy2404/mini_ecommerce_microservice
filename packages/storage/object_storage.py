# packages/storage/object_storage.py

from dataclasses import dataclass
from io import BytesIO
from urllib.parse import quote

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from packages.config.settings import Settings, get_settings


class ObjectStorageError(Exception):
    pass


@dataclass(frozen=True)
class UploadedObject:
    bucket_name: str
    object_key: str
    content_type: str
    url: str | None


class ObjectStorageClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

        client_kwargs: dict[str, object] = {
            "service_name": "s3",
            "region_name": settings.object_storage_region,
            "config": Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            ),
        }

        if settings.object_storage_endpoint_url:
            client_kwargs["endpoint_url"] = settings.object_storage_endpoint_url

        if (
            settings.object_storage_access_key_id
            and settings.object_storage_secret_access_key
        ):
            client_kwargs["aws_access_key_id"] = settings.object_storage_access_key_id
            client_kwargs["aws_secret_access_key"] = (
                settings.object_storage_secret_access_key
            )

        self._client = boto3.client(**client_kwargs)

    def upload_fileobj(
        self,
        file_buffer: BytesIO,
        object_key: str,
        content_type: str,
        cache_control: str = "public, max-age=31536000, immutable",
    ) -> UploadedObject:
        file_buffer.seek(0)

        try:
            self._client.upload_fileobj(
                file_buffer,
                self._settings.object_storage_bucket_name,
                object_key,
                ExtraArgs={
                    "ContentType": content_type,
                    "CacheControl": cache_control,
                },
            )
        except (BotoCoreError, ClientError) as exc:
            raise ObjectStorageError("Failed to upload object to storage.") from exc

        return UploadedObject(
            bucket_name=self._settings.object_storage_bucket_name,
            object_key=object_key,
            content_type=content_type,
            url=self.build_public_url(object_key),
        )

    def build_public_url(self, object_key: str) -> str | None:
        if not self._settings.object_storage_public_base_url:
            return None

        safe_key = quote(object_key)
        return f'{self._settings.object_storage_public_base_url.rstrip("/")}/{safe_key}'

    def create_presigned_get_url(self, object_key: str) -> str:
        try:
            return self._client.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    "Bucket": self._settings.object_storage_bucket_name,
                    "Key": object_key,
                },
                ExpiresIn=self._settings.object_storage_presigned_url_expire_seconds,
            )
        except (BotoCoreError, ClientError) as exc:
            raise ObjectStorageError("Failed to create presigned URL.") from exc


def get_object_storage_client() -> ObjectStorageClient:
    return ObjectStorageClient(get_settings())
