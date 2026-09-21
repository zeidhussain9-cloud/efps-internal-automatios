from __future__ import annotations

import pytest

try:
    from client import CloudinaryClient, CloudinaryCredentials, MissingCloudinaryCredentials
    from media import (
        catalog_urls,
        image_fingerprint,
        lead_public_id,
        property_public_id,
        upload_lead_images,
        upload_property_images,
    )
except ImportError:  # pragma: no cover - supports pytest from repository root
    from shared.cloudinary.client import CloudinaryClient, CloudinaryCredentials, MissingCloudinaryCredentials
    from shared.cloudinary.media import (
        catalog_urls,
        image_fingerprint,
        lead_public_id,
        property_public_id,
        upload_lead_images,
        upload_property_images,
    )


def test_missing_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "CLOUDINARY_CLOUD_NAME",
        "CLOUDINARY_API_KEY",
        "CLOUDINARY_API_SECRET",
        "CLOUDINARY_URL",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr("shared.cloudinary.client._secret_from_keychain", lambda: None)
    with pytest.raises(MissingCloudinaryCredentials):
        CloudinaryCredentials.from_environment()


def test_public_ids() -> None:
    assert property_public_id("EFPS-123", 1) == "properties/EFPS-123/photo_1"
    assert lead_public_id("919900000000", "msg-1", 2) == "leads/919900000000/msg-1_2"


def test_uploads_are_deterministic_and_injected() -> None:
    calls: list[dict] = []

    def fake_uploader(blob: bytes, **kwargs: object) -> dict[str, str]:
        calls.append({"blob": blob, **kwargs})
        return {"secure_url": f"https://res.cloudinary.test/{kwargs['public_id']}"}

    client = CloudinaryClient(
        CloudinaryCredentials("cloud", "key", "secret"), uploader=fake_uploader
    )
    uploads = upload_property_images(client, "EFPS-123", [b"a", b"b"])
    assert [u.public_id for u in uploads] == [
        "properties/EFPS-123/photo_1",
        "properties/EFPS-123/photo_2",
    ]
    assert calls[0]["overwrite"] is True


def test_lead_uploads_are_separate_namespace() -> None:
    def fake_uploader(blob: bytes, **kwargs: object) -> dict[str, str]:
        return {"secure_url": "https://example.test/image"}

    client = CloudinaryClient(
        CloudinaryCredentials("cloud", "key", "secret"), uploader=fake_uploader
    )
    uploads = upload_lead_images(client, "919900000000", "m-7", [b"a"])
    assert uploads[0].public_id.startswith("leads/")


def test_catalog_urls_limit() -> None:
    class U:
        def __init__(self, url: str) -> None:
            self.url = url

    uploads = [U(str(i)) for i in range(12)]
    assert catalog_urls(uploads).split(", ") == [str(i) for i in range(10)]


def test_property_reupload_overwrites_existing_asset() -> None:
    """Regression: overwrite=True ensures re-uploading the same public_id
    produces a new URL instead of silently returning the stale one."""
    call_count = 0

    def fake_uploader(blob: bytes, **kwargs: object) -> dict[str, str]:
        nonlocal call_count
        call_count += 1
        assert kwargs["overwrite"] is True
        return {"secure_url": f"https://res.cloudinary.test/{kwargs['public_id']}/v{call_count}"}

    client = CloudinaryClient(
        CloudinaryCredentials("cloud", "key", "secret"), uploader=fake_uploader
    )
    run1 = upload_property_images(client, "EF-TEST", [b"img1"])
    run2 = upload_property_images(client, "EF-TEST", [b"img2_different"])
    assert run1[0].public_id == run2[0].public_id
    assert run1[0].url != run2[0].url


def test_lead_upload_does_not_overwrite() -> None:
    """Lead uploads remain non-overwriting (different ownership semantics)."""
    calls: list[dict] = []

    def fake_uploader(blob: bytes, **kwargs: object) -> dict[str, str]:
        calls.append(dict(kwargs))
        return {"secure_url": "https://res.cloudinary.test/image"}

    client = CloudinaryClient(
        CloudinaryCredentials("cloud", "key", "secret"), uploader=fake_uploader
    )
    upload_lead_images(client, "919900000000", "m-1", [b"a"])
    assert calls[0]["overwrite"] is False


def test_fingerprint_is_stable() -> None:
    assert image_fingerprint(b"abc") == image_fingerprint(b"abc")
    assert image_fingerprint(b"abc") != image_fingerprint(b"abcd")
