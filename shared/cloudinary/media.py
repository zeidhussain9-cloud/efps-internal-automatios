"""Deterministic media naming and Cloudinary upload helpers."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .client import CloudinaryClient

MAX_CATALOG_IMAGES = 10


@dataclass(frozen=True)
class Upload:
    url: str
    public_id: str
    index: int


def property_public_id(listing_id: str, index: int) -> str:
    if not listing_id.strip():
        raise ValueError("listing_id must not be empty")
    if index < 1:
        raise ValueError("image index must be >= 1")
    return f"properties/{listing_id.strip()}/photo_{index}"


def lead_public_id(phone: str, message_id: str, index: int) -> str:
    if not phone.strip():
        raise ValueError("phone must not be empty")
    if index < 1:
        raise ValueError("image index must be >= 1")
    safe_message_id = "".join(
        c for c in str(message_id) if c.isalnum() or c in "-_"
    ) or "nomsg"
    return f"leads/{phone.strip()}/{safe_message_id}_{index}"


def upload_property_images(
    client: CloudinaryClient,
    listing_id: str,
    blobs: list[bytes],
    *,
    start_index: int = 1,
) -> list[Upload]:
    if start_index < 1:
        raise ValueError("start_index must be >= 1")
    result: list[Upload] = []
    for index, blob in enumerate(blobs, start=start_index):
        public_id = property_public_id(listing_id, index)
        payload = client.upload_bytes(blob, public_id=public_id, overwrite=False)
        result.append(
            Upload(
                url=str(payload["secure_url"]),
                public_id=public_id,
                index=index,
            )
        )
    return result


def upload_lead_images(
    client: CloudinaryClient,
    phone: str,
    message_id: str,
    blobs: list[bytes],
) -> list[Upload]:
    result: list[Upload] = []
    for index, blob in enumerate(blobs, start=1):
        public_id = lead_public_id(phone, message_id, index)
        payload = client.upload_bytes(blob, public_id=public_id, overwrite=False)
        result.append(
            Upload(
                url=str(payload["secure_url"]),
                public_id=public_id,
                index=index,
            )
        )
    return result


def catalog_urls(uploads: list[Upload]) -> str:
    """Return at most ten URLs, matching the verified legacy catalogue limit."""
    return ", ".join(upload.url for upload in uploads[:MAX_CATALOG_IMAGES])


def image_fingerprint(blob: bytes) -> str:
    if not blob:
        raise ValueError("Cannot fingerprint empty media")
    return hashlib.sha256(blob).hexdigest()[:16]
