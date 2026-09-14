"""Cloudinary transport wrapper.

Business modules decide when/why to upload. This module only provides reusable
technical Cloudinary operations and credential handling.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable


class MissingCloudinaryCredentials(RuntimeError):
    """Raised when required Cloudinary credentials are unavailable."""


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
        missing = [
            name
            for name, value in (
                ("CLOUDINARY_CLOUD_NAME", cloud_name),
                ("CLOUDINARY_API_KEY", api_key),
                ("CLOUDINARY_API_SECRET", api_secret),
            )
            if not value
        ]
        if missing:
            raise MissingCloudinaryCredentials(
                "Missing Cloudinary runtime configuration: " + ", ".join(missing)
            )
        return cls(cloud_name=cloud_name, api_key=api_key, api_secret=api_secret)


class CloudinaryClient:
    """Small dependency-injected Cloudinary client.

    The real SDK is imported lazily so unit tests can run without the SDK or
    network credentials. Callers may inject an uploader for deterministic tests.
    """

    def __init__(
        self,
        credentials: CloudinaryCredentials | None = None,
        *,
        uploader: Callable[..., dict[str, Any]] | None = None,
    ) -> None:
        self.credentials = credentials or CloudinaryCredentials.from_environment()
        self._uploader = uploader

    def _default_uploader(self) -> Callable[..., dict[str, Any]]:
        try:
            import cloudinary
            import cloudinary.uploader
        except ImportError as exc:
            raise RuntimeError(
                "The 'cloudinary' package is required for live uploads."
            ) from exc

        cloudinary.config(
            cloud_name=self.credentials.cloud_name,
            api_key=self.credentials.api_key,
            api_secret=self.credentials.api_secret,
            secure=True,
        )
        return cloudinary.uploader.upload

    def upload_bytes(
        self,
        blob: bytes,
        *,
        public_id: str,
        resource_type: str = "image",
        overwrite: bool = False,
    ) -> dict[str, Any]:
        if not blob:
            raise ValueError("Cannot upload an empty media blob.")
        uploader = self._uploader or self._default_uploader()
        return uploader(
            blob,
            public_id=public_id,
            resource_type=resource_type,
            overwrite=overwrite,
        )
