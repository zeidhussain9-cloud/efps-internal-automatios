"""Cloudinary transport wrapper with verified EFPS credential resolution."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Callable

SECRET_NAME = "efps-whapi-panel-cloudinary"


class MissingCloudinaryCredentials(RuntimeError):
    """Raised when required Cloudinary credentials are unavailable."""


def _secret_from_aws() -> dict[str, Any] | None:
    try:
        import boto3
        client = boto3.client("secretsmanager", region_name=os.environ.get("AWS_REGION", "us-east-1"))
        raw = client.get_secret_value(SecretId=SECRET_NAME).get("SecretString", "")
    except Exception:
        return None
    if not raw:
        return None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {"value": raw}
    return value if isinstance(value, dict) else {"value": value}


def _from_cloudinary_url(value: str) -> tuple[str, str, str]:
    try:
        rest = value.split("//", 1)[1]
        credentials, cloud_name = rest.split("@", 1)
        api_key, api_secret = credentials.split(":", 1)
    except (IndexError, ValueError) as exc:
        raise MissingCloudinaryCredentials("CLOUDINARY_URL is not a valid Cloudinary URL.") from exc
    return cloud_name, api_key, api_secret


@dataclass(frozen=True)
class CloudinaryCredentials:
    cloud_name: str
    api_key: str
    api_secret: str

    @classmethod
    def from_environment(cls) -> "CloudinaryCredentials":
        cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", "").strip()
        api_key = os.environ.get("CLOUDINARY_API_KEY", "").strip()
        api_secret = os.environ.get("CLOUDINARY_API_SECRET", "").strip()
        url = os.environ.get("CLOUDINARY_URL", "").strip()

        secret = _secret_from_aws()
        if secret:
            if not url:
                url = str(secret.get("CLOUDINARY_URL") or "").strip()
            cloud_name = cloud_name or str(secret.get("cloud_name") or "").strip()
            api_key = api_key or str(secret.get("api_key") or secret.get("CLOUDINARY_API_KEY") or "").strip()
            api_secret = api_secret or str(secret.get("api_secret") or secret.get("CLOUDINARY_API_SECRET") or "").strip()

        if url and (not api_key or not api_secret or not cloud_name):
            cloud_name, api_key, api_secret = _from_cloudinary_url(url)

        missing = [
            name for name, value in (
                ("CLOUDINARY_CLOUD_NAME", cloud_name),
                ("CLOUDINARY_API_KEY", api_key),
                ("CLOUDINARY_API_SECRET", api_secret),
            ) if not value
        ]
        if missing:
            raise MissingCloudinaryCredentials(
                f"No Cloudinary runtime credential. Expected AWS secret '{SECRET_NAME}' "
                f"or {', '.join(missing)} / CLOUDINARY_URL."
            )
        return cls(cloud_name=cloud_name, api_key=api_key, api_secret=api_secret)


class CloudinaryClient:
    """Small dependency-injected Cloudinary client."""

    def __init__(self, credentials: CloudinaryCredentials | None = None, *, uploader: Callable[..., dict[str, Any]] | None = None) -> None:
        self.credentials = credentials or CloudinaryCredentials.from_environment()
        self._uploader = uploader

    def _default_uploader(self) -> Callable[..., dict[str, Any]]:
        try:
            import cloudinary
            import cloudinary.uploader
        except ImportError as exc:
            raise RuntimeError("The 'cloudinary' package is required for live uploads.") from exc
        cloudinary.config(
            cloud_name=self.credentials.cloud_name,
            api_key=self.credentials.api_key,
            api_secret=self.credentials.api_secret,
            secure=True,
        )
        return cloudinary.uploader.upload

    def upload_bytes(self, blob: bytes, *, public_id: str, resource_type: str = "image", overwrite: bool = False) -> dict[str, Any]:
        if not blob:
            raise ValueError("Cannot upload an empty media blob.")
        uploader = self._uploader or self._default_uploader()
        return uploader(blob, public_id=public_id, resource_type=resource_type, overwrite=overwrite)
