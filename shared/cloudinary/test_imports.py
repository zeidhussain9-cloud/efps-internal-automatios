from __future__ import annotations

from shared.cloudinary.client import CloudinaryClient, CloudinaryCredentials
from shared.cloudinary.media import catalog_urls, image_fingerprint, lead_public_id, property_public_id


def test_cloudinary_imports_and_helpers() -> None:
    credentials = CloudinaryCredentials("cloud", "key", "secret")
    client = CloudinaryClient(credentials, uploader=lambda blob, **kwargs: {"secure_url": "https://x"})
    assert client.credentials == credentials
    assert property_public_id("L1", 1) == "properties/L1/photo_1"
    assert lead_public_id("1", "m", 1) == "leads/1/m_1"
    assert image_fingerprint(b"x")
    assert catalog_urls([]) == ""
