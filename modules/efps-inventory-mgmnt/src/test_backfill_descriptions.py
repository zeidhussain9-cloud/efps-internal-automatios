from src import backfill_descriptions as backfill


def test_generate_descriptions_copies_approved_catalogue_output(monkeypatch):
    row = {
        "listing_id": "EF-2611-TEST",
        "raw_message_text": "2 bathrooms. https://maps.app.goo.gl/AbCdEf123",
        "locality": "Haralur",
        "whatsapp_post": "*📍 Haralur:*\nhttps://maps.app.goo.gl/AbCdEf123",
        "catalogue_description": "Approved Catalogue text — preserve exactly.\nSecond line.",
        "whatsapp_group_description": "",
        "furnish_type": "Semi Furnished",
        "BHK": "2 BHK",
    }
    monkeypatch.setattr(backfill, "listing_snapshot", lambda page: row)
    captured = {}

    def group_builder(row, raw, **kwargs):
        captured.update(kwargs)
        return "Group output"

    monkeypatch.setattr(backfill, "build_whatsapp_group_description", group_builder)
    monkeypatch.setattr(backfill, "build_facebook_marketplace_description", lambda row, raw: "Facebook output")

    outputs, issues = backfill.generate_descriptions({"id": "page-id"})
    assert outputs["whatsapp_catalogue_description"] == row["catalogue_description"]
    assert outputs["whatsapp_group_description"] == "Group output"
    assert outputs["facebook_marketplace_description"] == "Facebook output"
    assert captured["maps_verified"] is True
    assert captured["verified_society_name"] == ""
    assert issues == []


def test_backfill_default_mode_is_read_only(monkeypatch):
    page = {"id": "page-id", "properties": {}}
    row = {
        "listing_id": "EF-2611-TEST",
        "whatsapp_group_description": "",
        "whatsapp_catalogue_description": "",
        "facebook_marketplace_description": "",
    }

    class FakeNotion:
        def __init__(self, token):
            assert token == "test-token"
        def validate_listing_schema(self):
            return {}
        def list_listings(self):
            return [page]
        def update_page(self, page_id, properties):
            raise AssertionError("Dry-run must never write to Notion")

    monkeypatch.setenv("NOTION_API_TOKEN", "test-token")
    monkeypatch.setattr(backfill, "NotionClient", FakeNotion)
    monkeypatch.setattr(backfill, "listing_snapshot", lambda page: row)
    monkeypatch.setattr(
        backfill,
        "generate_descriptions",
        lambda page: ({
            "whatsapp_group_description": "Group",
            "whatsapp_catalogue_description": "Catalogue",
            "facebook_marketplace_description": "Facebook",
        }, []),
    )

    result = backfill.run_backfill(apply=False, expected_count=1)
    assert result["summary"]["rows"] == 1
    assert result["summary"]["rows_to_update"] == 1
    assert result["summary"]["dry_run_only"] == 1
