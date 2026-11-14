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
    body = json.dumps({"id": "22345678-1234-4234-8234-123456789abc", "type": "page.created", "entity": {"id": "12345678-1234-4234-8234-123456789abc", "type": "page"}}, separators=(",", ":"))
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
    calls = []
    class FakeStore:
        def record_webhook_event(self, **event):
            calls.append(("record", event))
            return {"id": "notion-webhook:event:22345678-1234-4234-8234-123456789abc", "should_enqueue": True, "status": "received"}
        def update_webhook_event(self, event_row_id, status, **kwargs):
            calls.append((status, event_row_id, kwargs))
            return {"status": status, "started": status in {"accepted", "processing"}}
    monkeypatch.setenv("NOTION_SECRET_ARN", "arn:aws:secretsmanager:ap-southeast-2:123456789012:secret:test")
    monkeypatch.setattr("boto3.client", FakeBoto3.client, raising=False)
    monkeypatch.setattr(intake, "SupabaseIntakeStore", FakeStore)
    monkeypatch.setattr(intake, "_enqueue_worker", lambda page_id, arn, event_type="", event_id="", event_row_id="", attempt_number=None: (calls.append(("enqueue", event_row_id)), queued.append((page_id, arn, event_type, event_id, event_row_id))))
    context = type("Context", (), {"invoked_function_arn": "arn:aws:lambda:ap-southeast-2:123456789012:function:test"})()
    result = intake.lambda_handler({"headers": {"X-Notion-Signature": signature}, "body": body}, context)
    assert result["statusCode"] == 202
    assert queued == [("12345678-1234-4234-8234-123456789abc", context.invoked_function_arn, "page.created", "22345678-1234-4234-8234-123456789abc", "notion-webhook:event:22345678-1234-4234-8234-123456789abc")]
    assert [call[0] for call in calls] == ["record", "enqueue", "queued"]
    assert calls[0][1]["page_id"] == "12345678-1234-4234-8234-123456789abc"


def test_notion_webhook_rejects_invalid_native_signature(monkeypatch):
    class FakeSecrets:
        def get_secret_value(self, **kwargs):
            return {"SecretString": json.dumps({"api_token": "notion-api", "webhook_secret": "right-token"})}
    class FakeBoto3:
        @staticmethod
        def client(name):
            return FakeSecrets()
    class FakeStore:
        def __init__(self): self.recorded = []; self.transitions = []
        def record_webhook_event(self, **event):
            self.recorded.append(event)
            return {"id": "notion-webhook:event:22345678-1234-4234-8234-123456789abc", "should_enqueue": True}
        def update_webhook_event(self, event_row_id, status, **kwargs):
            self.transitions.append((event_row_id, status, kwargs))
            return {"status": status}
    store = FakeStore()
    monkeypatch.setenv("NOTION_SECRET_ARN", "arn:aws:secretsmanager:ap-southeast-2:123456789012:secret:test")
    monkeypatch.setattr("boto3.client", FakeBoto3.client, raising=False)
    monkeypatch.setattr(intake, "SupabaseIntakeStore", lambda: store)
    result = intake.lambda_handler({"headers": {"X-Notion-Signature": "sha256=wrong"}, "body": json.dumps({"entity": {"id": "12345678-1234-1234-1234-123456789abc"}})}, None)
    assert result["statusCode"] == 401
    assert store.recorded[0]["payload"]["unverified_delivery"] is True
    assert store.transitions[0][1] == "rejected"


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
                "id": page_id,
                "parent": {"database_id": intake.INTAKE_DATABASE_ID},
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
            return {"parent": {"database_id": intake.INTAKE_DATABASE_ID}, "properties": {"Raw Property Data": {"rich_text": [{"plain_text": "raw"}]}, "Photos": {"files": []}}}
    class FakeStore:
        def __init__(self): self.listing_ids = []
        def claim(self, page_id, payload_hash):
            return "duplicate", {"listing_id": "EF-EXISTING"}
        def find_inventory(self, page_id):
            return {"found": True, "listing_id": "EF-EXISTING"}
        def set_listing_id(self, page_id, listing_id): self.listing_ids.append((page_id, listing_id))
    class NoCalls:
        def __getattr__(self, name):
            raise AssertionError(f"unexpected call: {name}")
    store = FakeStore()
    result = intake.process_page(
        "intake-page-id", notion=FakeNotion(), store=store, sheets=NoCalls(),
        cloudinary=NoCalls(),
    )
    assert result == {"status": "already_processed", "listing_id": "EF-EXISTING"}
    assert store.listing_ids == [("intake-page-id", "EF-EXISTING")]


def test_processed_notion_page_repairs_a_missing_inventory_projection():
    page_id = "12345678-1234-1234-1234-123456789abc"
    page = {"id": page_id, "properties": {"listing_id": {"type": "rich_text", "rich_text": []}}}
    class FakeNotion:
        def __init__(self):
            self.updates = []
        def update_page(self, page_id, properties):
            self.updates.append((page_id, properties))
    class FakeStore:
        def __init__(self):
            self.synced = []
            self.finished = []
            self.listing_ids = []
        def set_listing_id(self, page_id, listing_id): self.listing_ids.append((page_id, listing_id))
        def claim(self, page_id, payload_hash):
            return "duplicate", {"listing_id": "EF-2611-ABCD"}
        def find_inventory(self, page_id):
            return {"found": False}
        def sync_inventory(self, page_id, row, *, deleted=False):
            self.synced.append((page_id, row, deleted))
        def finish(self, page_id, state, **kwargs):
            self.finished.append((state, kwargs))
    store = FakeStore()
    notion = FakeNotion()
    result = intake.process_listing_page(page, notion=notion, store=store)
    assert result == {"status": "synced", "listing_id": "EF-2611-ABCD"}
    assert len(store.synced) == 1
    assert store.synced[0][1]["listing_id"] == "EF-2611-ABCD"
    assert store.listing_ids == [(page_id, "EF-2611-ABCD")]
    assert notion.updates == [(page_id, {"listing_id": intake._rich("EF-2611-ABCD")})]
    assert store.finished[0][0] == "processed"

def test_duplicate_notion_page_restore_reactivates_soft_deleted_projection():
    page_id = "12345678-1234-1234-1234-123456789abc"
    page = {"id": page_id, "properties": {"listing_id": {"type": "rich_text", "rich_text": []}}}
    class FakeNotion:
        def __init__(self): self.updates = []
        def update_page(self, page_id, properties): self.updates.append((page_id, properties))
    class FakeStore:
        def __init__(self): self.synced = []; self.listing_ids = []
        def set_listing_id(self, page_id, listing_id): self.listing_ids.append((page_id, listing_id))
        def claim(self, page_id, payload_hash): return "duplicate", {"listing_id": "EF-2611-ABCD"}
        def find_inventory(self, page_id): return {"found": True, "listing_id": "EF-2611-ABCD", "deleted_at": "2026-11-13T10:00:00Z"}
        def sync_inventory(self, page_id, row, *, deleted=False): self.synced.append((row, deleted))
        def finish(self, page_id, state, **kwargs): pass
    notion, store = FakeNotion(), FakeStore()
    result = intake.process_listing_page(page, notion=notion, store=store)
    assert result == {"status": "synced", "listing_id": "EF-2611-ABCD"}
    assert len(store.synced) == 1 and store.synced[0][1] is False
    assert store.listing_ids == [(page_id, "EF-2611-ABCD")]
    assert notion.updates == [(page_id, {"listing_id": intake._rich("EF-2611-ABCD")})]


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
            return {"id": page_id, "parent": {"database_id": intake.INTAKE_DATABASE_ID}, "created_time": "2026-11-13T00:00:00Z", "properties": {
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
            return {"parent": {"database_id": intake.INTAKE_DATABASE_ID}, "properties": {"Raw Property Data": {"rich_text": [{"plain_text": "raw"}]}, "Photos": {"files": []}}}
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
    event_id = str(uuid.uuid4())
    body = json.dumps({"id": event_id, "type": "page.created", "entity": {"id": page_id, "type": "page"}}, separators=(",", ":"))
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
    class FakeStore:
        def record_webhook_event(self, **event): return {"id": "notion-webhook:event:" + event_id, "should_enqueue": True, "status": "accepted"}
        def update_webhook_event(self, *args, **kwargs):
            status = kwargs.get("status") or args[1]
            return {"status": status, "started": status in {"accepted", "processing"}}
    monkeypatch.setattr(intake, "SupabaseIntakeStore", FakeStore)
    monkeypatch.setattr(intake, "_enqueue_worker", lambda supplied, arn, event_type="", event_id="", event_row_id="", attempt_number=None: enqueued.append((supplied, arn, event_type, event_id, event_row_id)))
    context = type("Context", (), {"invoked_function_arn": "arn:aws:lambda:ap-southeast-2:123456789012:function:test"})()
    result = intake.lambda_handler({"headers": {"X-Notion-Signature": signature}, "body": body}, context)
    assert result["statusCode"] == 202
    assert enqueued[0][:4] == (page_id, context.invoked_function_arn, "page.created", event_id)
    assert enqueued[0][4]
    assert json.loads(result["body"])["accepted"] is True


def test_async_worker_invocation_runs_page_processor(monkeypatch):
    page_id = "12345678-1234-1234-1234-123456789abc"
    monkeypatch.setattr(intake, "process_page", lambda supplied, **kwargs: {"status": "Processed", "listing_id": "EF-ASYNC"} if supplied == page_id else {})
    result = intake.lambda_handler({"_efps_notion_worker": True, "page_id": page_id}, None)
    assert result["status"] == "Processed"
    assert result["listing_id"] == "EF-ASYNC"

def test_blank_raw_property_data_is_marked_needs_review_without_claiming():
    class FakeNotion:
        def __init__(self): self.updates = []
        def get_page(self, page_id):
            return {"parent": {"database_id": intake.INTAKE_DATABASE_ID}, "properties": {"Raw Property Data": {"rich_text": []}, "Photos": {"files": []}}}
        def update_page(self, page_id, properties): self.updates.append(properties)
    class NoCalls:
        def __getattr__(self, name): raise AssertionError(f"unexpected call: {name}")
    notion = FakeNotion()
    result = intake.process_page("12345678-1234-1234-1234-123456789abc", notion=notion,
                                 store=NoCalls(), sheets=NoCalls(), cloudinary=NoCalls())
    assert result["status"] == "Needs Review"
    assert notion.updates[0]["Intake Status"]["status"]["name"] == "Needs Review"


def test_listing_reconciliation_skips_unchanged_and_queues_soft_deleted_pages():
    pages = [
        {"id": "12345678-1234-1234-1234-123456789abc", "url": "https://notion.test/a", "last_edited_time": "2026-11-13T00:00:00Z",
         "properties": {"listing_id": {"type": "rich_text", "rich_text": [{"plain_text": "EF-2611-AAAA"}]}}},
        {"id": "22345678-1234-1234-1234-123456789abc", "url": "https://notion.test/b", "last_edited_time": "2026-11-13T00:00:00Z",
         "properties": {"listing_id": {"type": "rich_text", "rich_text": [{"plain_text": "EF-2611-BBBB"}]}}},
    ]
    class FakeNotion:
        def list_listings(self): return pages
    class FakeStore:
        def __init__(self): self.lookups = 0; self.reconciled = []
        def find_inventory(self, page_id):
            self.lookups += 1
            row = intake.listing_snapshot(pages[self.lookups - 1])
            digest = hashlib.sha256(json.dumps(row, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            if self.lookups == 1:
                return {"found": True, "listing_id": "EF-2611-AAAA", "deleted_at": None, "source_hash": digest}
            return {"found": True, "listing_id": "EF-2611-BBBB", "deleted_at": "2026-11-12T00:00:00Z", "source_hash": digest}
        def reconcile_pages(self, page_ids, listings): self.reconciled = page_ids; self.listings = listings; return {"listing_ids_reconciled": len(listings), "soft_deleted": 0}
    class FakeLambda:
        def __init__(self): self.payloads = []
        def invoke(self, **kwargs): self.payloads.append(json.loads(kwargs["Payload"])); return {"StatusCode": 202}
    store, client = FakeStore(), FakeLambda()
    result = intake._enqueue_listing_backfill("arn:aws:lambda:ap-southeast-2:123456789012:function:test", notion=FakeNotion(), store=store, lambda_client=client)
    assert result == {"checked": 2, "accepted": 1, "skipped_unchanged": 1, "listing_ids_reconciled": 2, "soft_deleted_missing": 0}
    assert client.payloads == [{"_efps_notion_worker": True, "page_id": pages[1]["id"], "event_type": "reconciliation"}]
    assert store.reconciled == [page["id"] for page in pages]
    assert store.listings == [
        {"page_id": pages[0]["id"], "listing_id": "EF-2611-AAAA"},
        {"page_id": pages[1]["id"], "listing_id": "EF-2611-BBBB"},
    ]


def test_listing_reconciliation_refuses_empty_notion_result():
    class FakeNotion:
        def list_listings(self): return []
    class NoCalls:
        def __getattr__(self, name): raise AssertionError(f"unexpected call: {name}")
    import pytest
    with pytest.raises(intake.IntakeError, match="zero pages"):
        intake._enqueue_listing_backfill("arn:test", notion=FakeNotion(), store=NoCalls(), lambda_client=NoCalls())


def test_notion_listing_reconciliation_excludes_archived_and_trashed_pages():
    class FakeResponse:
        ok = True
        content = b'{"results": [{"id": "active"}, {"id": "archived", "archived": true}, {"id": "trashed", "in_trash": true}], "has_more": false}'
        def json(self): return json.loads(self.content)
    class FakeSession:
        def request(self, *args, **kwargs): return FakeResponse()
    notion = intake.NotionClient("test-token", session=FakeSession())
    assert [page["id"] for page in notion.list_listings()] == ["active"]
