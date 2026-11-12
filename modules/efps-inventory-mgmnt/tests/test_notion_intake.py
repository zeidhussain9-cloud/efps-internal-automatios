from __future__ import annotations

import hashlib
import hmac
import json

from src import notion_intake as intake


def test_bhk_group_uses_the_verified_five_destinations():
    assert intake._bhk_group("1 RK")[0] == "1 RK / 1–1.5 BHK"
    assert intake._bhk_group("1.5 BHK")[0] == "1 RK / 1–1.5 BHK"
    assert intake._bhk_group("2.5 BHK")[0] == "2 / 2.5 BHK"
    assert intake._bhk_group("3 BHK")[0] == "3 / 3.5 BHK"
    assert intake._bhk_group("4.5 BHK")[0] == "4 / 4.5 BHK"
    assert intake._bhk_group("5 BHK")[0] == "5+ BHK"
    assert intake._bhk_group("2 BHK")[1] == "https://chat.whatsapp.com/BphJsvDKuVyHJ7Em1P4CYC"
    assert intake._bhk_group("2 BHK Villa")[0] == ""


def test_listing_projection_maps_canonical_types_and_ignores_reserved_columns():
    row = {
        "listing_id": "EF-TEST-1", "catalog_title": "2 BHK Apartment", "BHK": "2 BHK",
        "property_subtype": "Apartment", "monthly_rent": "50000", "pet_friendly": "Yes",
        "servant_room": "No", "maintenance_included": "Yes", "google_maps_url": "",
        "source_group": "must-not-write", "inventory_locked": "must-not-write",
    }
    props = intake.listing_notion_properties(row)
    assert props["Property"]["title"][0]["text"]["content"] == "2 BHK Apartment"
    assert props["monthly_rent"]["number"] == 50000
    assert props["pet_friendly"]["checkbox"] is True
    assert props["servant_room"]["checkbox"] is False
    assert props["maintenance_included"]["checkbox"] is True
    assert props["WhatsApp Group"]["select"]["name"] == "2 / 2.5 BHK"
    assert props["WhatsApp Destination"]["url"] == "https://chat.whatsapp.com/BphJsvDKuVyHJ7Em1P4CYC"
    assert "source_group" not in props
    assert "inventory_locked" not in props


def test_listing_projection_does_not_guess_missing_values():
    props = intake.listing_notion_properties({"listing_id": "EF-TEST-2", "BHK": "", "monthly_rent": ""})
    assert "WhatsApp Group" not in props
    assert "WhatsApp Destination" not in props
    assert "monthly_rent" not in props


def test_download_image_rejects_non_notion_hosts_before_network():
    import pytest
    with pytest.raises(intake.IntakeError, match="Notion-hosted"):
        intake._download_image("https://example.com/photo.jpg")


def test_webhook_requires_configured_secret(monkeypatch):
    monkeypatch.delenv("NOTION_WEBHOOK_SECRET", raising=False)
    result = intake.lambda_handler({"headers": {"x-efps-notion-intake-token": "anything"}, "body": "{}"}, None)
    assert result["statusCode"] == 401


def test_webhook_rejects_invalid_page_id_after_authorization(monkeypatch):
    monkeypatch.setenv("NOTION_WEBHOOK_SECRET", "secret-value")
    result = intake.lambda_handler(
        {"headers": {"X-EFPS-Notion-Intake-Token": "secret-value"}, "body": json.dumps({"page_id": "not-a-page"})},
        None,
    )
    assert result["statusCode"] == 400


def test_photo_resume_reuploads_full_ordered_set_to_deterministic_ids(monkeypatch):
    calls = []
    monkeypatch.setattr(intake, "_download_image", lambda url: b"image")
    def upload(client, listing_id, blobs, *, start_index):
        calls.append(start_index)
        return [intake.Upload(url=f"https://res.cloudinary.com/{start_index}.jpg", public_id=f"photo_{start_index}", index=start_index)]
    monkeypatch.setattr(intake, "upload_property_images", upload)
    page = {"properties": {"Photos": {"files": [{"type": "file", "file": {"url": "https://secure.notion-static.com/a"}}, {"type": "file", "file": {"url": "https://secure.notion-static.com/b"}}]}}}
    urls, issues = intake._upload_photos(page, "EF-TEST-3", {"cloudinary_image_urls": "https://res.cloudinary.com/a.jpg"}, object())
    assert urls == ["https://res.cloudinary.com/1.jpg", "https://res.cloudinary.com/2.jpg"]
    assert calls == [1, 2]
    assert issues == []

def test_process_page_persists_one_listing_and_reconciles_intake(monkeypatch):
    class FakeNotion:
        def __init__(self):
            self.updates = []
            self.saved = []
        def get_page(self, page_id):
            return {
                "created_time": "2026-11-13T00:00:00Z",
                "properties": {
                    "Raw Property Data": {"rich_text": [{"plain_text": "2 BHK Apartment\\nRent: 50000\\nLocation: Harlur"}]},
                    "Photos": {"files": []},
                    "Listing ID": {"rich_text": []},
                },
            }
        def update_page(self, page_id, properties):
            self.updates.append(properties)
        def save_listing(self, row):
            self.saved.append(row)
            return "housing-page-id"

    class FakeStore:
        def __init__(self):
            self.finished = []
        def claim(self, page_id, payload_hash):
            return "claimed", {"listing_id": "EF-TEST-INTAKE"}
        def set_listing_id(self, page_id, listing_id):
            raise AssertionError("existing listing ID should be reused")
        def finish(self, page_id, state, **kwargs):
            self.finished.append((state, kwargs))

    class FakeSheets:
        def __init__(self):
            self.inserts = []
            self.writes = []
        def read_range(self, spreadsheet_id, worksheet_name, range_name):
            return []
        def insert_rows(self, spreadsheet_id, worksheet_name, rows):
            self.inserts.extend(rows)
        def write_ranges(self, spreadsheet_id, worksheet_name, updates):
            self.writes.extend(updates)

    fake_notion, fake_store, fake_sheets = FakeNotion(), FakeStore(), FakeSheets()
    def fake_pipeline(raw_text, *, row, maps_client):
        result = dict(row)
        result.update(status="Pending", intake_status="Processed", property_subtype="Apartment", raw_message_text=raw_text)
        return result, []
    monkeypatch.setattr(intake.pipeline, "process_closed_session", fake_pipeline)
    result = intake.process_page(
        "intake-page-id", notion=fake_notion, store=fake_store, sheets=fake_sheets,
        cloudinary=object(), maps_client=object(),
    )
    assert result["status"] == "Processed"
    assert result["listing_id"] == "EF-TEST-INTAKE"
    assert len(fake_sheets.inserts) == 1
    assert fake_sheets.writes
    assert fake_notion.saved[0]["listing_id"] == "EF-TEST-INTAKE"
    final = fake_notion.updates[-1]
    assert final["Intake Status"]["status"]["name"] == "Processed"
    assert final["Processed Property"]["relation"][0]["id"] == "housing-page-id"
    assert fake_store.finished[0][0] == "processed"


def test_process_page_duplicate_delivery_does_not_write(monkeypatch):
    class FakeNotion:
        def get_page(self, page_id):
            return {"properties": {"Raw Property Data": {"rich_text": [{"plain_text": "raw"}]}, "Photos": {"files": []}}}
    class FakeStore:
        def claim(self, page_id, payload_hash):
            return "duplicate", {"listing_id": "EF-EXISTING"}
    class NoCalls:
        def __getattr__(self, name):
            raise AssertionError(f"unexpected call: {name}")
    result = intake.process_page(
        "intake-page-id", notion=FakeNotion(), store=FakeStore(), sheets=NoCalls(),
        cloudinary=NoCalls(),
    )
    assert result == {"status": "already_processed", "listing_id": "EF-EXISTING"}

def test_photo_upload_retry_reuses_deterministic_indexes(monkeypatch):
    calls = []
    monkeypatch.setattr(intake, "_download_image", lambda url: url.encode())
    def upload(client, listing_id, blobs, *, start_index):
        calls.append((listing_id, blobs[0], start_index))
        return [intake.Upload(url=f"https://res.cloudinary.com/{start_index}.jpg", public_id=f"photo_{start_index}", index=start_index)]
    monkeypatch.setattr(intake, "upload_property_images", upload)
    page = {"properties": {"Photos": {"files": [
        {"type": "file", "file": {"url": "https://secure.notion-static.com/a"}},
        {"type": "file", "file": {"url": "https://secure.notion-static.com/b"}},
    ]}}}
    urls, issues = intake._upload_photos(page, "EF-TEST-4", {"cloudinary_image_urls": ""}, object())
    assert urls == ["https://res.cloudinary.com/1.jpg", "https://res.cloudinary.com/2.jpg"]
    assert issues == []
    assert [x[2] for x in calls] == [1, 2]


def test_photo_upload_partial_failure_does_not_publish_incomplete_url_set(monkeypatch):
    monkeypatch.setattr(intake, "_download_image", lambda url: url.encode())
    def upload(client, listing_id, blobs, *, start_index):
        if start_index == 1:
            raise RuntimeError("temporary")
        return [intake.Upload(url="https://res.cloudinary.com/2.jpg", public_id="photo_2", index=2)]
    monkeypatch.setattr(intake, "upload_property_images", upload)
    page = {"properties": {"Photos": {"files": [
        {"type": "file", "file": {"url": "https://secure.notion-static.com/a"}},
        {"type": "file", "file": {"url": "https://secure.notion-static.com/b"}},
    ]}}}
    urls, issues = intake._upload_photos(page, "EF-TEST-5", {"cloudinary_image_urls": ""}, object())
    assert urls == []
    assert len(issues) == 1
    assert "Photo 1" in issues[0]