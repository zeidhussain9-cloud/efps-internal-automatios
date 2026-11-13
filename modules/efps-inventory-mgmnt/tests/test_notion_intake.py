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


def test_notion_api_token_is_loaded_from_secrets_manager(monkeypatch):
    class FakeSecrets:
        def get_secret_value(self, **kwargs):
            return {"SecretString": json.dumps({"api_token": "runtime-token", "webhook_secret": "webhook-token"})}
    class FakeBoto3:
        @staticmethod
        def client(name):
            assert name == "secretsmanager"
            return FakeSecrets()
    monkeypatch.setenv("NOTION_SECRET_ARN", "arn:aws:secretsmanager:ap-southeast-2:123456789012:secret:test")
    monkeypatch.setattr("boto3.client", FakeBoto3.client, raising=False)
    assert intake._notion_secret_value("api_token") == "runtime-token"


def test_notion_webhook_verification_handshake_persists_verification_token(monkeypatch):
    calls = []
    class FakeSecrets:
        def get_secret_value(self, **kwargs):
            return {"SecretString": json.dumps({"api_token": "notion-api", "webhook_secret": "generated-placeholder"})}
        def put_secret_value(self, **kwargs):
            calls.append(json.loads(kwargs["SecretString"]))
    class FakeBoto3:
        @staticmethod
        def client(name):
            assert name == "secretsmanager"
            return FakeSecrets()
    monkeypatch.setenv("NOTION_SECRET_ARN", "arn:aws:secretsmanager:ap-southeast-2:123456789012:secret:test")
    monkeypatch.setattr("boto3.client", FakeBoto3.client, raising=False)
    body = json.dumps({"verification_token": "notion-verification-token"}, separators=(",", ":"))
    signature = "sha256=" + hmac.new(b"notion-verification-token", body.encode(), hashlib.sha256).hexdigest()
    result = intake.lambda_handler({"headers": {"X-Notion-Signature": signature}, "body": body}, None)
    assert result["statusCode"] == 200
    assert calls[0]["api_token"] == "notion-api"
    assert calls[0]["webhook_secret"] == "notion-verification-token"


def test_notion_webhook_rejects_invalid_verification_handshake(monkeypatch):
    class FakeSecrets:
        def get_secret_value(self, **kwargs):
            return {"SecretString": json.dumps({"api_token": "notion-api", "webhook_secret": "old-token"})}
        def put_secret_value(self, **kwargs):
            raise AssertionError("invalid handshake must not update the secret")
    class FakeBoto3:
        @staticmethod
        def client(name): return FakeSecrets()
    monkeypatch.setenv("NOTION_SECRET_ARN", "arn:aws:secretsmanager:ap-southeast-2:123456789012:secret:test")
    monkeypatch.setattr("boto3.client", FakeBoto3.client, raising=False)
    body = json.dumps({"verification_token": "attacker-token"})
    result = intake.lambda_handler({"headers": {"X-Notion-Signature": "sha256=wrong"}, "body": body}, None)
    assert result["statusCode"] == 401


def test_notion_webhook_validates_native_signature_and_queues_page(monkeypatch):
    body = json.dumps({"type": "page.created", "entity": {"id": "12345678-1234-1234-1234-123456789abc"}}, separators=(",", ":"))
    token = "notion-verification-token"
    signature = "sha256=" + hmac.new(token.encode(), body.encode(), hashlib.sha256).hexdigest()
    class FakeSecrets:
        def get_secret_value(self, **kwargs):
            return {"SecretString": json.dumps({"api_token": "notion-api", "webhook_secret": token})}
    class FakeBoto3:
        @staticmethod
        def client(name):
            return FakeSecrets()
    queued = []
    monkeypatch.setenv("NOTION_SECRET_ARN", "arn:aws:secretsmanager:ap-southeast-2:123456789012:secret:test")
    monkeypatch.setattr("boto3.client", FakeBoto3.client, raising=False)
    monkeypatch.setattr(intake, "_enqueue_worker", lambda page_id, arn: queued.append((page_id, arn)))
    context = type("Context", (), {"invoked_function_arn": "arn:aws:lambda:ap-southeast-2:123456789012:function:test"})()
    result = intake.lambda_handler({"headers": {"X-Notion-Signature": signature}, "body": body}, context)
    assert result["statusCode"] == 202
    assert queued[0][0] == "12345678-1234-1234-1234-123456789abc"


def test_notion_webhook_rejects_invalid_native_signature(monkeypatch):
    class FakeSecrets:
        def get_secret_value(self, **kwargs):
            return {"SecretString": json.dumps({"api_token": "notion-api", "webhook_secret": "right-token"})}
    class FakeBoto3:
        @staticmethod
        def client(name):
            return FakeSecrets()
    monkeypatch.setenv("NOTION_SECRET_ARN", "arn:aws:secretsmanager:ap-southeast-2:123456789012:secret:test")
    monkeypatch.setattr("boto3.client", FakeBoto3.client, raising=False)
    result = intake.lambda_handler({"headers": {"X-Notion-Signature": "sha256=wrong"}, "body": json.dumps({"entity": {"id": "12345678-1234-1234-1234-123456789abc"}})}, None)
    assert result["statusCode"] == 401


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
def test_v71_caption_uses_verified_short_map_and_never_guesses_pet_policy():
    row = {"furnish_type": "Semi Furnished", "BHK": "2 BHK", "monthly_rent": "50000",
           "security_deposit": "125000", "built_up_area": "1200", "floor_number": "3",
           "total_floors": "12", "preferred_tenant_type": "Anyone", "pet_friendly": "Yes",
           "internal_property_type": "Gated Community", "locality": "Kasavanahalli",
           "google_maps_url": "https://maps.app.goo.gl/AbC123", "bathrooms": "2", "balconies": "2"}
    raw = "Pets allowed\nAvailability: Ready to Occupy\n2 attached bathrooms\nUtility"
    caption = intake.build_whatsapp_post(row, raw, maps_verified=True, verified_society_name="Verified Society")
    assert caption.startswith("*👉Semi Furnished 2 BHK with Utility & 2 Attached Bathrooms & 2 Balconies*")
    assert "Rent: 50K" in caption and "Deposit: 1.25L" in caption
    assert "Available from: Ready to Occupy" in caption
    assert "Preferred tenant: Open For All" in caption
    assert "Pets: Allowed\nGated Community\nLocation: *Kasavanahalli*" in caption
    assert "*📍 Verified Society:\nhttps://maps.app.goo.gl/AbC123" in caption


def test_v71_caption_requires_maps_verification_and_omits_long_map_url():
    row = {"furnish_type": "Fully Furnished", "BHK": "1 BHK", "locality": "Harlur",
           "google_maps_url": "https://maps.app.goo.gl/AbC123"}
    assert intake.build_whatsapp_post(row, "Pets allowed", maps_verified=False) == ""
    row["google_maps_url"] = "https://www.google.com/maps/search/?api=1&query=Harlur"
    caption = intake.build_whatsapp_post(row, "Pets allowed", maps_verified=True)
    assert "google.com/maps" not in caption and "Location: *Harlur*" in caption
    assert "Pets: Allowed" in caption


def test_v71_caption_does_not_infer_pet_policy_from_inventory_default():
    row = {"furnish_type": "Semi Furnished", "BHK": "2 BHK", "locality": "Harlur", "pet_friendly": "Yes"}
    assert "Pets:" not in intake.build_whatsapp_post(row, "2 BHK Apartment", maps_verified=True)


def test_supabase_intake_store_claims_through_supabase_edge_function(monkeypatch):
    calls = []
    class Response:
        ok = True
        def json(self): return {"status": "claimed", "item": {"listing_id": "EF-TEST"}}
    class FakeSession:
        def post(self, url, **kwargs):
            calls.append((url, kwargs))
            return Response()
    monkeypatch.setenv("SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "public-anon-key")
    store = intake.SupabaseIntakeStore("internal-notion-token", session=FakeSession())
    status, item = store.claim("12345678-1234-1234-1234-123456789abc", "hash")
    assert status == "claimed" and item["listing_id"] == "EF-TEST"
    url, request = calls[0]
    assert url == "https://project.supabase.co/functions/v1/notion-inventory-state"
    assert request["headers"]["Authorization"] == "Bearer public-anon-key"
    assert request["headers"]["X-EFPS-Intake-Auth"] == "internal-notion-token"
    assert request["json"]["operation"] == "claim"


def test_process_page_persists_one_listing_and_reconciles_intake(monkeypatch):
    class FakeNotion:
        def __init__(self): self.updates, self.saved = [], []
        def get_page(self, page_id):
            return {"created_time": "2026-11-13T00:00:00Z", "properties": {
                "Raw Property Data": {"rich_text": [{"plain_text": "2 BHK Apartment\nRent: 50000\nLocation: Harlur"}]},
                "Photos": {"files": []}, "Listing ID": {"rich_text": []}}}
        def update_page(self, page_id, properties): self.updates.append(properties)
        def save_listing(self, row): self.saved.append(row); return "housing-page-id"
    class FakeStore:
        def __init__(self): self.finished = []
        def claim(self, page_id, payload_hash): return "claimed", {"listing_id": "EF-TEST-INTAKE"}
        def set_listing_id(self, page_id, listing_id): raise AssertionError("existing ID should be reused")
        def finish(self, page_id, state, **kwargs): self.finished.append((state, kwargs))
    class FakeSheets:
        def __init__(self): self.inserts, self.writes = [], []
        def read_range(self, spreadsheet_id, worksheet_name, range_name): return []
        def insert_rows(self, spreadsheet_id, worksheet_name, rows): self.inserts.extend(rows)
        def write_ranges(self, spreadsheet_id, worksheet_name, updates): self.writes.extend(updates)
    fake_notion, fake_store, fake_sheets = FakeNotion(), FakeStore(), FakeSheets()
    def fake_pipeline(raw_text, *, row, maps_client):
        result = dict(row)
        result.update(status="Pending", intake_status="Processed", property_subtype="Apartment",
                      raw_message_text=raw_text, locality="Harlur", BHK="2 BHK",
                      furnish_type="Semi Furnished", monthly_rent="50000")
        return result, []
    monkeypatch.setattr(intake.pipeline, "process_closed_session", fake_pipeline)
    result = intake.process_page("intake-page-id", notion=fake_notion, store=fake_store,
                                 sheets=fake_sheets, cloudinary=object(), maps_client=object())
    assert result["status"] == "Processed" and result["listing_id"] == "EF-TEST-INTAKE"
    assert len(fake_sheets.inserts) == 1 and fake_sheets.writes
    assert fake_notion.saved[0]["whatsapp_post"].startswith("*👉Semi Furnished 2 BHK*")
    assert fake_notion.saved[0]["whatsapp_post"].endswith("Location: *Harlur*")
    assert fake_notion.updates[-1]["Intake Status"]["status"]["name"] == "Processed"
    assert fake_notion.updates[-1]["Processed Property"]["relation"][0]["id"] == "housing-page-id"
    assert fake_store.finished[0][0] == "processed"


def test_process_page_duplicate_delivery_does_not_write():
    class FakeNotion:
        def get_page(self, page_id):
            return {"properties": {"Raw Property Data": {"rich_text": [{"plain_text": "raw"}]}, "Photos": {"files": []}}}
    class FakeStore:
        def claim(self, page_id, payload_hash): return "duplicate", {"listing_id": "EF-EXISTING"}
    class NoCalls:
        def __getattr__(self, name): raise AssertionError(f"unexpected call: {name}")
    result = intake.process_page("intake-page-id", notion=FakeNotion(), store=FakeStore(),
                                 sheets=NoCalls(), cloudinary=NoCalls())
    assert result == {"status": "already_processed", "listing_id": "EF-EXISTING"}

def test_webhook_accepts_notion_event_entity_id(monkeypatch):
    import hashlib, hmac, uuid
    page_id = str(uuid.uuid4())
    token = "notion-webhook-verification-token"
    body = json.dumps({"type": "page.created", "entity": {"id": page_id}}, separators=(",", ":"))
    signature = "sha256=" + hmac.new(token.encode(), body.encode(), hashlib.sha256).hexdigest()
    class FakeSecrets:
        def get_secret_value(self, **kwargs):
            return {"SecretString": json.dumps({"api_token": "notion-api", "webhook_secret": token})}
    class FakeBoto3:
        @staticmethod
        def client(name): return FakeSecrets()
    monkeypatch.setenv("NOTION_SECRET_ARN", "arn:aws:secretsmanager:ap-southeast-2:123456789012:secret:test")
    monkeypatch.setattr("boto3.client", FakeBoto3.client, raising=False)
    enqueued = []
    monkeypatch.setattr(intake, "_enqueue_worker", lambda supplied, arn: enqueued.append((supplied, arn)))
    context = type("Context", (), {"invoked_function_arn": "arn:aws:lambda:ap-southeast-2:123456789012:function:test"})()
    result = intake.lambda_handler({"headers": {"X-Notion-Signature": signature}, "body": body}, context)
    assert result["statusCode"] == 202
    assert enqueued == [(page_id, context.invoked_function_arn)]
    assert json.loads(result["body"])["accepted"] is True


def test_async_worker_invocation_runs_page_processor(monkeypatch):
    page_id = "12345678-1234-1234-1234-123456789abc"
    monkeypatch.setattr(intake, "process_page", lambda supplied: {"status": "Processed", "listing_id": "EF-ASYNC"} if supplied == page_id else {})
    result = intake.lambda_handler({"_efps_notion_worker": True, "page_id": page_id}, None)
    assert result["status"] == "Processed"
    assert result["listing_id"] == "EF-ASYNC"

def test_blank_raw_property_data_is_marked_needs_review_without_claiming():
    class FakeNotion:
        def __init__(self): self.updates = []
        def get_page(self, page_id):
            return {"properties": {"Raw Property Data": {"rich_text": []}, "Photos": {"files": []}}}
        def update_page(self, page_id, properties): self.updates.append(properties)
    class NoCalls:
        def __getattr__(self, name): raise AssertionError(f"unexpected call: {name}")
    notion = FakeNotion()
    result = intake.process_page("12345678-1234-1234-1234-123456789abc", notion=notion,
                                 store=NoCalls(), sheets=NoCalls(), cloudinary=NoCalls())
    assert result["status"] == "Needs Review"
    assert notion.updates[0]["Intake Status"]["status"]["name"] == "Needs Review"
