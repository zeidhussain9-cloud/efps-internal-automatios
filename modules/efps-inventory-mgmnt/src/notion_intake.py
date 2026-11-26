"""Idempotent Notion property intake adapter over the canonical Inventory pipeline."""
from __future__ import annotations

import difflib
import hashlib
import hmac
import json
import os
import re
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

import requests

from shared.cloudinary.client import CloudinaryClient, CloudinaryCredentials
from shared.cloudinary.media import Upload, upload_property_images, catalog_urls
from shared.ola_maps.links import MapsLinks
from shared.ola_maps.inventory import OlaInventoryMaps
from shared.google_sheets import schema
from shared.ola_maps import OlaMapsClient

try:
    from . import pipeline, notion_lifecycle, extract as area_extract
    from .location_match import normalize_locality
    from .normalize import build_catalog_title
    from .description_generators import build_whatsapp_group_description, build_facebook_marketplace_description
except ImportError:
    import pipeline, notion_lifecycle
    import extract as area_extract
    from location_match import normalize_locality
    from normalize import build_catalog_title
    from description_generators import build_whatsapp_group_description, build_facebook_marketplace_description

NOTION_VERSION = "2022-06-28"
INTAKE_DATABASE_ID = "89dad7a3990849ca9dc23e5bcb3fa99f"
LISTINGS_DATABASE_ID = "bccfd4f55e294b269daa093a928f873a"
CATALOGUE_PANEL_DATABASE_ID = "41ffedf9b4e8815fb6cfd2ffe275110d"
MAX_IMAGES = 10
MAX_IMAGE_BYTES = 20 * 1024 * 1024
ALLOWED_FILE_HOSTS = {"secure.notion-static.com", "prod-files-secure.s3.us-west-2.amazonaws.com"}


class IntakeError(RuntimeError):
    pass


def _log_event(event: str, **fields):
    """Emit structured, non-secret operational evidence for every Notion event."""
    print(json.dumps({"service": "efps-notion-intake", "event": event, **fields}, sort_keys=True, default=str))


def _is_missing_notion_page_error(error: Exception) -> bool:
    text = str(error).lower()
    return "object_not_found" in text or ("failed (404)" in text and "pages/" in text)


class NotionClient:
    def __init__(self, token: str, *, session=None):
        if not token:
            raise IntakeError("NOTION_API_TOKEN is not configured")
        self.token = token
        self.session = session or requests.Session()

    def request(self, method: str, path: str, *, payload=None):
        delay = 2.0
        for _attempt in range(5):
            response = self.session.request(
                method,
                "https://api.notion.com/v1/" + path.lstrip("/"),
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Notion-Version": NOTION_VERSION,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=25,
            )
            if getattr(response, "status_code", 200) != 429:
                break
            # Notion rate limit: honor retry-after, bounded exponential backoff.
            retry_after = 0.0
            try:
                retry_after = float(response.headers.get("Retry-After") or 0)
            except (TypeError, ValueError):
                retry_after = 0.0
            try:
                retry_after = max(retry_after, float((response.json().get("additional_data") or {}).get("retry_after") or 0))
            except (TypeError, ValueError):
                pass
            time.sleep(min(max(retry_after, delay), 30.0))
            delay = min(delay * 2, 30.0)
        if not response.ok:
            try:
                error = response.json()
            except ValueError:
                error = {}
            code = str(error.get("code") or "")[:100]
            message = str(error.get("message") or "")[:600]
            detail = ": ".join(part for part in (code, message) if part)
            suffix = f": {detail}" if detail else ""
            raise IntakeError(f"Notion API {method} {path} failed ({response.status_code}){suffix}")
        return response.json() if response.content else {}

    def get_page(self, page_id: str):
        return self.request("GET", f"pages/{page_id}")

    def validate_listing_schema(self):
        """Fail before external writes if the canonical Housing Listings schema drifted."""
        database = self.request("GET", f"databases/{LISTINGS_DATABASE_ID}")
        schema = database.get("properties") or {}
        validate_listing_schema(schema)
        self._listing_schema = schema
        return schema

    def update_page(self, page_id: str, properties: dict):
        return self.request("PATCH", f"pages/{page_id}", payload={"properties": properties})

    def find_listing(self, listing_id: str):
        result = self.request(
            "POST",
            f"databases/{LISTINGS_DATABASE_ID}/query",
            payload={"filter": {"property": "listing_id", "rich_text": {"equals": listing_id}}, "page_size": 1},
        )
        rows = result.get("results") or []
        return rows[0] if rows else None

    def list_listings(self):
        pages, cursor = [], None
        while True:
            payload = {"page_size": 100}
            if cursor:
                payload["start_cursor"] = cursor
            result = self.request("POST", f"databases/{LISTINGS_DATABASE_ID}/query", payload=payload)
            pages.extend(
                page for page in (result.get("results") or [])
                if not page.get("archived") and not page.get("in_trash")
            )
            if not result.get("has_more"):
                return pages
            cursor = result.get("next_cursor")
            if not cursor:
                raise IntakeError("Notion Housing Listings pagination returned no cursor")

    def upload_file(self, data: bytes, filename: str, content_type: str = "image/jpeg") -> str:
        """Create a Notion file upload, send the bytes, return the upload id."""
        created = self.request("POST", "file_uploads", payload={"filename": filename, "content_type": content_type})
        upload_id = str(created.get("id") or "")
        if not upload_id:
            raise IntakeError("Notion file upload was not created")
        response = self.session.post(
            f"https://api.notion.com/v1/file_uploads/{upload_id}/send",
            headers={"Authorization": f"Bearer {self.token}", "Notion-Version": NOTION_VERSION},
            files={"file": (filename, data, content_type)},
            timeout=60,
        )
        if not response.ok or str(response.json().get("status") or "") != "uploaded":
            raise IntakeError(f"Notion file upload failed ({response.status_code})")
        return upload_id

    def save_listing(self, row: dict):
        # Read and validate the live Notion schema before constructing any write payload.
        # The serializer uses the actual property type, so a Select conversion cannot
        # silently be sent as rich_text (or vice versa).
        schema = getattr(self, "_listing_schema", None) or self.validate_listing_schema()
        existing = self.find_listing(str(row["listing_id"]))
        row = dict(row)
        if existing:
            latest = listing_snapshot(existing)
            # Re-read at the write boundary, not only before slow media processing.
            for key in ("Availability", "live at", "meta_catalog_id", "posted_url", "posted_at", "error_notes"):
                row[key] = latest.get(key, [] if key == "live at" else "")
            if row.get("Pipeline Status") != "Needs Review" and latest.get("Pipeline Status") in {"Posted", "Removed"}:
                row["Pipeline Status"] = latest["Pipeline Status"]
        properties = listing_notion_properties(row, schema=schema)
        # Native Photos column: Notion-hosted copies of the intake photos (same as the
        # manual native uploads), attached only when this run uploaded a fresh set.
        upload_ids = [x for x in (row.get("_native_photo_upload_ids") or []) if x]
        if upload_ids and (schema.get("Photos") or {}).get("type") == "files":
            slug = str(row.get("listing_id") or "photo")
            properties["Photos"] = {"files": [
                {"name": f"{slug}-{i:02d}.jpg", "type": "file_upload", "file_upload": {"id": fid}}
                for i, fid in enumerate(upload_ids, start=1)]}
        validate_listing_properties(schema, properties)
        enforce_select_vocabulary(schema, properties)
        if existing:
            self.update_page(existing["id"], properties)
            return existing["id"]
        result = self.request(
            "POST",
            "pages",
            payload={"parent": {"database_id": LISTINGS_DATABASE_ID}, "properties": properties},
        )
        return result["id"]


class SupabaseIntakeStore:
    """Durable Notion idempotency state in the production Supabase project."""
    def __init__(self, internal_key: str = "", *, session=None):
        self.url = os.environ.get("SUPABASE_URL", "").rstrip("/")
        self.anon_key = os.environ.get("SUPABASE_ANON_KEY", "")
        self.internal_key = internal_key or _notion_secret_value("api_token")
        self.session = session or requests.Session()
        if not self.url or not self.anon_key or not self.internal_key:
            raise IntakeError("Supabase inventory intake endpoint credentials are not configured")

    def _request(self, operation: str, **payload):
        response = self.session.post(
            f"{self.url}/functions/v1/notion-inventory-state",
            headers={
                "apikey": self.anon_key,
                "Authorization": f"Bearer {self.anon_key}",
                "X-EFPS-Intake-Auth": self.internal_key,
                "Content-Type": "application/json",
            },
            json={"operation": operation, **payload},
            timeout=20,
        )
        if not response.ok:
            raise IntakeError(f"Supabase inventory idempotency request failed ({response.status_code})")
        return response.json()

    def claim(self, page_id: str, payload_hash: str):
        result = self._request("claim", page_id=page_id, payload_hash=payload_hash)
        return str(result.get("status") or "in_progress"), result.get("item") or {}

    def set_listing_id(self, page_id: str, listing_id: str):
        self._request("set_listing_id", page_id=page_id, listing_id=listing_id)

    def allocate_listing_id(self, page_id: str):
        last_error = None
        for attempt in range(3):
            try:
                listing_id = str(self._request("allocate_listing_id", page_id=page_id).get("listing_id") or "").strip()
                if listing_id:
                    return listing_id
                last_error = IntakeError("Supabase Listing ID allocator returned an empty result")
            except IntakeError as exc:
                last_error = exc
            if attempt < 2:
                time.sleep(0.15 * (attempt + 1))
        raise IntakeError(f"Supabase Listing ID allocation failed after 3 attempts: {last_error}")

    def sync_inventory(self, page_id: str, row: dict, *, deleted: bool = False):
        source_hash = hashlib.sha256(json.dumps(row, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self._request("sync_inventory", page_id=page_id, listing_id=row["listing_id"], row=row, source_hash=source_hash, deleted=deleted)

    def delete_inventory(self, page_id: str):
        return self._request("delete_inventory", page_id=page_id)

    def find_inventory(self, page_id: str):
        return self._request("find_inventory", page_id=page_id)

    def reconcile_pages(self, page_ids: list[str], listings: list[dict]):
        return self._request("reconcile_pages", active_page_ids=page_ids, active_listings=listings)

    def finish(self, page_id: str, state: str, *, listing_page_id: str = "", note: str = ""):
        self._request("finish", page_id=page_id, state=state, listing_page_id=listing_page_id, note=note[:1800])

    def record_webhook_event(self, **event):
        return self._request("record_webhook_event", **event)

    def update_webhook_event(
        self,
        event_row_id: str,
        status: str,
        *,
        aws_request_id: str = "",
        error: str = "",
        outcome: dict | None = None,
        page_id: str = "",
        listing_id: str = "",
        listing_page_id: str = "",
    ):
        return self._request(
            "update_webhook_event",
            event_row_id=event_row_id,
            status=status,
            aws_request_id=aws_request_id,
            error=error[:1800],
            outcome=outcome,
            page_id=page_id or None,
            listing_id=listing_id,
            listing_page_id=listing_page_id or None,
        )


def _plain_text(value: dict) -> str:
    return "".join(str(x.get("plain_text") or x.get("text", {}).get("content") or "") for x in value.get("rich_text", []))


def _title(page: dict) -> str:
    props = page.get("properties") or {}
    title = props.get("Intake Entry", {}).get("title") or []
    return "".join(str(x.get("plain_text") or x.get("text", {}).get("content") or "") for x in title).strip()


def _photos(page: dict) -> list[dict]:
    return list((page.get("properties") or {}).get("Photos", {}).get("files") or [])


def _notion_value(prop: dict) -> str:
    """Flatten a canonical Housing Listings property without inventing values."""
    kind = str(prop.get("type") or "")
    value = prop.get(kind)
    if kind in {"title", "rich_text"}:
        return "".join(str(part.get("plain_text") or part.get("text", {}).get("content") or "") for part in (value or []))
    if kind == "number":
        return "" if value is None else str(value)
    if kind == "checkbox":
        return "Yes" if value else "No"
    if kind in {"select", "status"}:
        return str((value or {}).get("name") or "")
    if kind == "multi_select":
        return ", ".join(str(part.get("name") or "") for part in (value or []) if part.get("name"))
    if kind in {"url", "email", "phone_number"}:
        return str(value or "")
    if kind == "date":
        return str((value or {}).get("start") or "")
    return ""


def listing_snapshot(page: dict) -> dict:
    """Project one Housing Listings page into the existing dashboard snapshot contract."""
    properties = page.get("properties") or {}
    # The last two schema slots are reserved and must not be read from Notion.
    row = {name: _notion_value(properties.get(name) or {}) for name in schema.NAMES[:-2]
           if name not in notion_lifecycle.LEGACY_STATUS_FIELDS}
    for name in notion_lifecycle.CANONICAL_FIELDS:
        row[name] = _notion_value(properties.get(name) or {})
    row["live at"] = [str(x.get("name") or "") for x in (properties.get("live at", {}).get("multi_select") or [])]
    for name in ("Property", "WhatsApp Group", "whatsapp_post", "catalogue_description",
                 "whatsapp_group_description", "whatsapp_catalogue_description",
                 "facebook_marketplace_description", "WhatsApp Destination"):
        row[name] = _notion_value(properties.get(name) or {})
    row["notion_page_id"] = str(page.get("id") or "")
    row["notion_url"] = str(page.get("url") or "")
    row["notion_edited_at"] = str(page.get("last_edited_time") or "")
    return row


def _file_url(item: dict) -> str:
    kind = item.get("type")
    if kind == "file":
        return str((item.get("file") or {}).get("url") or "")
    if kind == "external":
        return str((item.get("external") or {}).get("url") or "")
    return ""


def _allowed_file_host(host: str | None) -> bool:
    host = (host or "").lower()
    return host in ALLOWED_FILE_HOSTS or host.endswith(".s3.amazonaws.com") or host.endswith(".s3.us-west-2.amazonaws.com")


def _download_image(url: str, *, session=None) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not _allowed_file_host(parsed.hostname):
        raise IntakeError("Photo URL is not a supported Notion-hosted HTTPS file")
    client = session or requests.Session()
    response = client.get(url, timeout=30, stream=True, allow_redirects=True)
    redirect_urls = [x.url for x in response.history] + [response.url]
    if any(urlparse(target).scheme != "https" or not _allowed_file_host(urlparse(target).hostname) for target in redirect_urls):
        raise IntakeError("Notion photo redirect left the supported file hosts")
    if response.status_code != 200:
        raise IntakeError(f"Notion photo download failed ({response.status_code})")
    content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
    if not content_type.startswith("image/"):
        raise IntakeError("Attached file is not an image")
    length = int(response.headers.get("Content-Length") or 0)
    if length > MAX_IMAGE_BYTES:
        raise IntakeError("Attached image exceeds the 20 MB limit")
    chunks, total = [], 0
    for chunk in response.iter_content(64 * 1024):
        if not chunk:
            continue
        total += len(chunk)
        if total > MAX_IMAGE_BYTES:
            raise IntakeError("Attached image exceeds the 20 MB limit")
        chunks.append(chunk)
    return b"".join(chunks)


def _number(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _rich(value: object) -> dict:
    text = str(value or "")
    parts = [text[i:i + 1900] for i in range(0, len(text), 1900)] or [""]
    return {"rich_text": [{"type": "text", "text": {"content": part}} for part in parts[:100]]}


def _append_processing_notes(notion: NotionClient, page_id: str, note: str) -> str:
    """Append one processing outcome to the existing Notion cell without replacing history."""
    page = notion.get_page(page_id)
    props = page.get("properties") or {}
    existing = _plain_text(props.get("Processing Notes") or {}).strip()
    addition = str(note or "").strip()
    combined = "\n".join(part for part in (existing, addition) if part)
    return combined


def _bhk_group(bhk: str):
    value = str(bhk or "").strip().upper()
    if value == "1 RK":
        return "1 RK / 1–1.5 BHK", "https://chat.whatsapp.com/Gd4qdmCDaB24xTKWJNjcx3"
    match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*BHK", value)
    if not match:
        return "", ""
    n = float(match.group(1))
    if n in (1, 1.5):
        return "1 RK / 1–1.5 BHK", "https://chat.whatsapp.com/Gd4qdmCDaB24xTKWJNjcx3"
    if n in (2, 2.5):
        return "2 / 2.5 BHK", "https://chat.whatsapp.com/BphJsvDKuVyHJ7Em1P4CYC"
    if n in (3, 3.5):
        return "3 / 3.5 BHK", "https://chat.whatsapp.com/L5EjmcPCDvJ6vMGvB3eDfU"
    if n in (4, 4.5):
        return "4 / 4.5 BHK", "https://chat.whatsapp.com/EuvjOdWJ0Yn7wvXmgNopZ8"
    if n >= 5:
        return "5+ BHK", "https://chat.whatsapp.com/LJK1w1Rc8mJDi1yS5jb5po"
    return "", ""


TEXT_FIELDS = {
    "BHK", "catalog_title", "catalogue_description", "whatsapp_group_description",
    "whatsapp_catalogue_description", "facebook_marketplace_description", "city", "cloudinary_image_urls",
    "error_notes", "flat_furnishings", "floor_number", "furnish_type", "intake_status",
    "internal_property_type", "landmark", "listing_id", "locality",
    "maintenance", "meta_catalog_id", "meta_catalog_status", "onboarded_on", "open_parking",
    "posted_at", "property_highlights", "property_subtype",
    "raw_message_text", "society_amenities", "society_name", "status", "transaction_type",
    "whatsapp_post",
} - notion_lifecycle.LEGACY_STATUS_FIELDS
NUMBER_FIELDS = {
    "age_of_property_years", "balconies", "bathrooms", "built_up_area", "carpet_area",
    "covered_parking", "monthly_rent", "pincode", "security_deposit", "total_floors",
}
URL_FIELDS = {"google_maps_url", "posted_url", "whatsapp_contact_link", "whatsapp_group_link"}


def listing_property_types() -> dict[str, str]:
    return {
        "Property": "title",
        **{field: "rich_text" for field in TEXT_FIELDS},
        **{field: "number" for field in NUMBER_FIELDS},
        **{field: "url" for field in URL_FIELDS},
        **{field: "checkbox" for field in ("pet_friendly", "servant_room", "maintenance_included")},
        "locality": "select",
        "preferred_tenant_type": "select",
        "bachelor_preference": "select",
        "bachelor_display": "formula",
        "Availability": "select",
        "Pipeline Status": "select",
        "live at": "multi_select",
        "WhatsApp Group": "select",
        "WhatsApp Destination": "url",
    }


def validate_listing_properties(schema: dict, properties: dict) -> None:
    errors = []
    for name, payload in properties.items():
        expected = next(iter(payload), "")
        definition = schema.get(name) or {}
        actual = str(definition.get("type") or "missing")
        if actual != expected:
            errors.append(f"{name}: expected {expected}, found {actual}")
            continue
        if expected in {"select", "status"}:
            selected = str((payload.get(expected) or {}).get("name") or "").strip()
            options = {
                str(option.get("name") or "")
                for option in (definition.get(expected) or {}).get("options", [])
            }
            if selected and selected not in options:
                errors.append(f"{name}: {expected} option {selected!r} is not defined in Notion")
    if errors:
        raise IntakeError("Housing Listings schema validation failed: " + "; ".join(errors))


def validate_listing_schema(schema: dict) -> None:
    expected = listing_property_types()
    # String-valued inventory fields can legitimately be represented by different
    # Notion text-like property types. Validate the live type, then serialize against
    # that exact type; do not hard-code rich_text for every string field.
    dynamic_text_fields = TEXT_FIELDS - {"listing_id"}
    errors = [
        f"{name}: expected {kind}, found {str((schema.get(name) or {}).get('type') or 'missing')}"
        for name, kind in expected.items()
        if name not in dynamic_text_fields
        and str((schema.get(name) or {}).get("type") or "missing") != kind
    ]
    for name in sorted(dynamic_text_fields):
        actual = str((schema.get(name) or {}).get("type") or "missing")
        if actual not in {"rich_text", "select", "status"}:
            errors.append(f"{name}: expected a supported text-like property (rich_text, select, or status), found {actual}")
    for name, values in {
        "Availability": set(notion_lifecycle.AVAILABILITY),
        "Pipeline Status": set(notion_lifecycle.PIPELINE),
        "preferred_tenant_type": {"Family Only", "Open For All"},
        "bachelor_preference": {"Female Only", "Male Only", "Open for both"},
        "WhatsApp Group": {
            "1 RK / 1–1.5 BHK", "2 / 2.5 BHK", "3 / 3.5 BHK",
            "4 / 4.5 BHK", "5+ BHK",
        },
    }.items():
        definition = schema.get(name) or {}
        options = {str(option.get("name") or "") for option in (definition.get("select") or {}).get("options", [])}
        missing = sorted(values - options)
        if missing:
            errors.append(f"{name}: missing select options {', '.join(missing)}")
    channel_options = {str(x.get("name") or "") for x in (schema.get("live at", {}).get("multi_select", {}).get("options") or [])}
    if not set(notion_lifecycle.CHANNELS).issubset(channel_options):
        errors.append("live at: missing canonical channel options")
    if errors:
        raise IntakeError("Housing Listings schema validation failed: " + "; ".join(errors))


def _serialize_text_field(value: object, property_type: str, field: str) -> dict:
    """Serialize a string-valued field according to its fetched Notion property type."""
    text = str(value or "").strip()
    if property_type == "rich_text":
        return _rich(text)
    if property_type == "select":
        return {"select": {"name": text}} if text else {"select": None}
    if property_type == "status":
        return {"status": {"name": text}} if text else {"status": None}
    raise IntakeError(f"Unsupported live Notion text property type for {field}: {property_type}")


def listing_notion_properties(row: dict, *, schema: dict | None = None) -> dict:
    """Project supported fields using the live Notion property types; reserved fields stay omitted."""
    title = str(row.get("catalog_title") or row.get("listing_id") or "").strip()[:2000]
    properties = {"Property": {"title": [{"type": "text", "text": {"content": title}}]}}
    fallback_types = listing_property_types()
    for field in TEXT_FIELDS:
        property_type = str(((schema or {}).get(field) or {}).get("type") or fallback_types[field])
        properties[field] = _serialize_text_field(row.get(field, ""), property_type, field)
    for field in ("Availability", "Pipeline Status"):
        if field in row:
            properties[field] = {"select": {"name": row[field]}} if row[field] else {"select": None}
    for field in ("preferred_tenant_type", "bachelor_preference"):
        if field in row:
            value = str(row.get(field) or "").strip()
            properties[field] = {"select": {"name": value}} if value else {"select": None}
    if "live at" in row:
        channels = row["live at"]
        if not isinstance(channels, list) or any(x not in notion_lifecycle.CHANNELS for x in channels):
            raise IntakeError("Invalid live at channel list")
        properties["live at"] = {"multi_select": [{"name": x} for x in channels]}
    for field in NUMBER_FIELDS:
        value = _number(row.get(field))
        if value is not None:
            properties[field] = {"number": value}
    for field in URL_FIELDS:
        value = str(row.get(field) or "").strip()
        properties[field] = {"url": value or None}
    for field in ("pet_friendly", "servant_room", "maintenance_included"):
        value = str(row.get(field) or "").strip().lower()
        if value in {"yes", "no"}:
            properties[field] = {"checkbox": value == "yes"}
    group, destination = _bhk_group(row.get("BHK", ""))
    if group:
        properties["WhatsApp Group"] = {"select": {"name": group}}
        properties["WhatsApp Destination"] = {"url": destination}
    # Reserved source columns are intentionally omitted from this projection.
    return properties



def _compact_amount(value: object) -> str:
    try:
        amount = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, TypeError, ValueError):
        return str(value or "").strip()
    if amount == 0:
        return "0"
    if amount >= 100000:
        text = format(amount / Decimal(100000), "f")
        text = text.rstrip("0").rstrip(".") if "." in text else text
        return f"{text}L"
    if amount >= 1000:
        text = format(amount / Decimal(1000), "f")
        text = text.rstrip("0").rstrip(".") if "." in text else text
        return f"{text}K"
    text = format(amount, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _short_mobile_maps_url(url: str) -> bool:
    parsed = urlparse(str(url or "").strip())
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and (host in {"maps.app.goo.gl", "share.google"} or (host == "goo.gl" and parsed.path.startswith("/maps")))


def _explicit_pet_policy(raw_text: str) -> str:
    text = str(raw_text or "")
    if re.search(r"\b(?:no\s+pets?|pets?\s*(?::|=|-)?\s*(?:are\s*)?not\s+allowed|pets?\s*(?::|=|-)?\s*prohibited|not\s+pet\s+friendly)\b", text, re.I):
        return "Not Allowed"
    if re.search(r"\b(?:pets?\s*(?::|=|-)?\s*(?:are\s*)?allowed|pet\s+friendly|pets?\s*(?::|=|-)?\s*welcome|(?:only\s+)?(?:one|\d+)\s+pets?\s+allowed)\b", text, re.I):
        return "Allowed"
    return ""


def _available_from(raw_text: str) -> str:
    text = str(raw_text or "")
    match = re.search(r"\b(?:available\s+from|available\s+on|availability)\s*[:\-]\s*([^\n\r]+)", text, re.I)
    if not match:
        return "Ready to Occupy" if re.search(r"\b(?:ready\s+to\s+occupy|immediately\s+available|available\s+immediately)\b", text, re.I) else ""
    value = match.group(1).strip(" .;")
    return "Ready to Occupy" if re.search(r"\b(?:now|immediate|immediately|ready\s+to\s+occupy)\b", value, re.I) else value


def _rupee_amount(value: object) -> str:
    """Full Indian-grouped amount for catalogue captions (125000 -> '1,25,000')."""
    try:
        amount = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, TypeError, ValueError):
        return ""
    if amount <= 0:
        return ""
    text = str(int(amount))
    if len(text) <= 3:
        return text
    head, tail = text[:-3], text[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    return ",".join(groups) + "," + tail


def _advertised_sqft(row: dict, raw_text: str = "") -> str:
    """The area figure the ad itself gave: a labelled built-up value when the ad labelled one,
    otherwise the carpet figure (labelled carpet or plain Sqft)."""
    carpet = str(row.get("carpet_area") or "").strip()
    built = str(row.get("built_up_area") or "").strip()
    basis = area_extract.area_basis(raw_text or str(row.get("raw_message_text") or ""))
    if basis == "built_up" and built:
        return built
    return carpet or built


def build_whatsapp_post(row: dict, raw_text: str, *, maps_verified: bool, verified_society_name: str = "", allow_unverified_source_map: bool = False, resolved_maps_url: str = "") -> str:
    """Build the card-style catalogue caption from explicit facts.

    Template approved by Zeid (21 Nov, "Option B"): emoji-labelled lines in
    blank-line sections, rupee amounts written out in full, map link last.
    Lines and sections appear only when their data exists; an unverified
    source URL is opt-in and remains labelled unverified; no verified map
    link or no locality means no caption at all (fail safe).

    resolved_maps_url is the canonical google.com/maps/search caption link
    produced by the pipeline from the expanded source link. When present it
    is the only map link the caption carries: short goo.gl/share.google URLs
    never reach a post.
    """
    maps_url = str(row.get("google_maps_url") or "").strip()
    resolved_maps_url = str(resolved_maps_url or "").strip()
    if maps_url and not maps_verified and not allow_unverified_source_map and not resolved_maps_url:
        return ""
    if allow_unverified_source_map and maps_url and not _short_mobile_maps_url(maps_url) and not resolved_maps_url:
        return ""
    locality = str(row.get("locality") or "").strip()
    if not locality:
        return ""

    base = " ".join(x for x in (str(row.get("furnish_type") or "").strip(), str(row.get("BHK") or "").strip()) if x)
    if base:
        headline = f"*🏠 {base} - {locality}*"
    else:
        fallback = str(row.get("catalog_title") or row.get("listing_id") or "").strip()
        if not fallback:
            return ""
        headline = f"*🏠 {fallback}*"

    raw = str(raw_text or "")
    features = []
    if re.search(r"\bprivate\s+terrace\b", raw, re.I):
        features.append("private terrace")
    if re.search(r"\butility\b", raw, re.I):
        features.append("utility")
    attached = re.search(r"\b(\d+)\s+attached\s+bathrooms?\b", raw, re.I)
    if attached:
        features.append(f"{attached.group(1)} attached bathrooms")
    elif row.get("bathrooms"):
        count = str(row["bathrooms"]).strip()
        features.append(f"{count} bathroom" + ("" if count == "1" else "s"))
    balconies = str(row.get("balconies") or "").strip()
    if balconies and balconies not in {"0", "0.0"}:
        features.append(f"{balconies} " + ("balcony" if balconies == "1" else "balconies"))
    features = features[:3]

    sections = [headline]

    money = []
    rent = _rupee_amount(row.get("monthly_rent"))
    maintenance = str(row.get("maintenance") or "").strip()
    included = str(row.get("maintenance_included") or "").strip().lower() == "yes"
    if rent:
        line = f"💰 Rent: Rs {rent}"
        if included:
            line += " (maintenance included)"
        money.append(line)
    if maintenance and not included:
        amount = _rupee_amount(maintenance)
        money.append(f"🧾 Maintenance: Rs {amount}" if amount else f"🧾 Maintenance: {maintenance}")
    deposit = _rupee_amount(row.get("security_deposit"))
    if deposit:
        money.append(f"🔑 Deposit: Rs {deposit}")
    if money:
        sections.append("\n".join(money))

    specs = []
    sqft = _advertised_sqft(row, raw_text)
    floor = str(row.get("floor_number") or "").strip()
    total_floors = str(row.get("total_floors") or "").strip()
    if floor and total_floors and "/" not in floor and floor.lower() not in {"villa", "independent house", "duplex"}:
        floor = f"{floor}/{total_floors}"
    spec_parts = []
    if sqft:
        spec_parts.append(f"{sqft} sqft")
    if floor:
        spec_parts.append(f"Floor {floor}")
    if spec_parts:
        specs.append("📐 " + " | ".join(spec_parts))
    if features:
        specs.append("🛁 " + " + ".join(features))
    availability = _available_from(raw)
    if availability:
        specs.append(f"🗓️ Available: {availability}")
    if specs:
        sections.append("\n".join(specs))

    people = []
    tenant = str(row.get("preferred_tenant_type") or "").strip()
    if tenant:
        if tenant.lower() in {"anyone", "open for all"}:
            people.append("👥 Open For All")
        else:
            people.append(f"👨‍👩‍👧 {tenant}")
    pets = _explicit_pet_policy(raw)
    if pets:
        people.append(f"🐾 Pets: {pets}")
    internal_type = str(row.get("internal_property_type") or "").strip()
    if internal_type == "Gated Community":
        people.append("🏢 Gated community")
    elif internal_type == "Semi Gated":
        people.append("🏘️ Semi gated community")
    if people:
        sections.append("\n".join(people))

    society = str(verified_society_name or row.get("society_name") or "").strip()
    label = society if society and society.casefold() != locality.casefold() else locality
    if resolved_maps_url:
        sections.append(f"*📍 {label}:*\n{resolved_maps_url}")
    elif maps_url and _short_mobile_maps_url(maps_url):
        if allow_unverified_source_map and not maps_verified:
            sections.append(f"*📍 Original Maps link (not verified):*\n{maps_url}")
        else:
            sections.append(f"*📍 {label}:*\n{maps_url}")
    return "\n\n".join(sections)


_MONTH_LOOKUP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _ordinal(n: int) -> str:
    """1st, 2nd, 3rd, 4th... with the 11th/12th/13th exception."""
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}" + {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def _catalogue_availability(value: str, *, today) -> str:
    """Zeid's 21 Nov rule: a future date in full ('1st December 2026');
    anything present or past is 'Ready To Occupy'. Unparseable text is
    preserved verbatim, never rewritten into a guess."""
    text = str(value or "").strip()
    if not text:
        return ""
    if re.search(r"\bready\s*to\s*occupy\b", text, re.I):
        return "Ready To Occupy"
    day = month = year = None
    m = re.search(r"(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?([A-Za-z]+)\s*,?\s*(\d{4})?", text)
    if m:
        day, mon, year = int(m.group(1)), m.group(2), m.group(3)
    else:
        m = re.search(r"([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?\s*,?\s*(\d{4})?", text)
        if m:
            mon, day, year = m.group(1), int(m.group(2)), m.group(3)
    if day is None:
        return text
    month = _MONTH_LOOKUP.get(mon.lower()[:3])
    if not month:
        return text
    year = int(year) if year else today.year
    try:
        d = datetime(year, month, day).date()
    except ValueError:
        return text
    if d <= today:
        return "Ready To Occupy"
    return f"{_ordinal(day)} {datetime(year, month, day).strftime('%B')} {year}"


def build_catalogue_description(row: dict, raw_text: str, *, verified_society_name: str = "", verified_landmark_name: str = "", resolved_maps_url: str = "", today=None) -> str:
    """Catalogue product description per the rules Zeid stamped on 21 Nov 2026.

    Option B card style. Product name is the standardized catalog_title.
    Floors use proper ordinals ('3rd of 5th floors', just '3rd' when the
    total is unknown). Maintenance is one of Rs amount / Included / Water
    Charges Additional. Availability is a full future date or 'Ready To
    Occupy'. Tenant type uses the locked LOV only. Locked 24 Nov 3:05 PM
    (Zeid): when the row has a society name, the description closes with
    it; otherwise with the bare "*Landmark:*" label. Superseded 24 Nov
    8:33 PM (Zeid): no Maps link in the description at all (it goes only to
    the product link field); society ending is "*📍<society>:*", no-society
    ending is "*📍Landmark:*" (corrected 8:53 PM: pin, no space). A society equal to the locality is
    the pipeline fallback and never renders as a name. Lines
    render only when their data exists.
    """
    # Rebuild even when called directly on an existing, stale row.
    title = build_catalog_title(row) if row.get("locality") else str(row.get("catalog_title") or row.get("listing_id") or "").strip()
    if not title:
        return ""
    raw = str(raw_text or "")
    sections = [f"*🏠 {title}*"]

    money = []
    rent = _rupee_amount(row.get("monthly_rent"))
    included = str(row.get("maintenance_included") or "").strip().lower() == "yes"
    if rent:
        line = f"💰 Rent: Rs {rent}"
        if included:
            line += " (maintenance included)"
        money.append(line)
    maintenance = str(row.get("maintenance") or "").strip()
    if maintenance and not included:
        amount = _rupee_amount(maintenance)
        if amount:
            money.append(f"🧾 Maintenance: Rs {amount}")
        elif re.search(r"\bwater\b", maintenance, re.I):
            money.append("🧾 Maintenance: Water Charges Additional")
        else:
            money.append(f"🧾 Maintenance: {maintenance}")
    deposit = _rupee_amount(row.get("security_deposit"))
    if deposit:
        money.append(f"🔑 Deposit: Rs {deposit}")
    if money:
        sections.append("\n".join(money))

    specs = []
    spec_parts = []
    sqft = _advertised_sqft(row, raw_text)
    if sqft:
        spec_parts.append(f"{sqft} sqft")
    floor = str(row.get("floor_number") or "").strip()
    total_floors = str(row.get("total_floors") or "").strip()
    if floor and floor.lower() not in {"villa", "independent house", "duplex"}:
        if floor.isdigit() and total_floors.isdigit():
            spec_parts.append(f"Floor {_ordinal(int(floor))} of {_ordinal(int(total_floors))} floors")
        elif floor.isdigit():
            spec_parts.append(f"Floor {_ordinal(int(floor))}")
        else:
            spec_parts.append(f"Floor {floor}")
    elif floor:
        spec_parts.append(floor)
    if spec_parts:
        specs.append("📐 " + " | ".join(spec_parts))
    features = []
    if re.search(r"\bprivate\s+terrace\b", raw, re.I):
        features.append("private terrace")
    if re.search(r"\butility\b", raw, re.I):
        features.append("utility")
    attached = re.search(r"\b(\d+)\s+attached\s+bathrooms?\b", raw, re.I)
    if attached:
        features.append(f"{attached.group(1)} attached bathrooms")
    elif row.get("bathrooms"):
        count = str(row["bathrooms"]).strip()
        features.append(f"{count} bathroom" + ("" if count == "1" else "s"))
    balconies = str(row.get("balconies") or "").strip()
    if balconies and balconies not in {"0", "0.0"}:
        features.append(f"{balconies} " + ("balcony" if balconies == "1" else "balconies"))
    features = features[:3]
    if features:
        specs.append("🛁 " + " + ".join(features))
    availability = _catalogue_availability(_available_from(raw), today=today or datetime.now(timezone.utc).date())
    if availability:
        specs.append(f"🗓️ Available: {availability}")
    if specs:
        sections.append("\n".join(specs))

    people = []
    tenant = str(row.get("preferred_tenant_type") or "").strip()
    if tenant.lower() in {"family", "family only"}:
        people.append("👨‍👩‍👧 Family Only")
    elif tenant.lower() in {"anyone", "open for all"}:
        people.append("👥 Open For All")
    pets = _explicit_pet_policy(raw)
    if pets:
        people.append(f"🐾 Pets: {pets}")
    internal_type = str(row.get("internal_property_type") or "").strip()
    if internal_type == "Gated Community":
        people.append("🏢 Gated community")
    elif internal_type == "Semi Gated":
        people.append("🏘️ Semi gated community")
    if people:
        sections.append("\n".join(people))

    # Locked 24 Nov (Zeid): the description closes with the society name when
    # the row has a real one, otherwise "Landmark: <landmark>", each followed
    # by the long map link. The pipeline stores the locality itself in
    # society_name/landmark when no real name was extracted (phase1 location
    # contract). Zeid 3:09 PM: society_name equal to the locality is that
    # fallback, never a real society - skip it; landmark is always used as-is
    # for the ending, including when it holds the locality fallback value.
    locality = str(row.get("locality") or "").strip()
    society = str(verified_society_name or "").strip()
    if not society:
        candidate_society = str(row.get("society_name") or "").strip()
        if candidate_society and candidate_society.lower() != locality.lower():
            society = candidate_society
            # The locality dropdown normalisation can respell the locality ("Harlur" ->
            # "Haralur") while the stored fallback keeps the raw spelling. A society that
            # equals the landmark and is a near-identical spelling of the locality is that
            # same fallback, not a real society name.
            if (candidate_society.lower() == str(row.get("landmark") or "").strip().lower()
                    and locality
                    and difflib.SequenceMatcher(None, candidate_society.lower(), locality.lower()).ratio() >= 0.85):
                society = ""
    landmark = str(verified_landmark_name or "").strip()
    if not landmark:
        landmark = str(row.get("landmark") or "").strip()
    # Zeid 24 Nov 8:33 PM: the description carries NO Maps link. The link
    # reaches the catalogue only through the product's separate link field
    # (google_maps_url). The ending is the label alone: with a society,
    # "*📍<society>:*"; otherwise "*📍Landmark:*" (pin, no space; corrected
    # by Zeid 24 Nov 8:53 PM, the missing pin was his own miss).
    if society:
        sections.append(f"*📍{society}:*")
    else:
        sections.append("*📍Landmark:*")
    return "\n\n".join(sections)


def _upload_photos(page: dict, listing_id: str, row: dict, cloudinary: CloudinaryClient):
    files = _photos(page)
    existing = [x.strip() for x in str(row.get("cloudinary_image_urls") or "").split(",") if x.strip()]
    if len(files) > MAX_IMAGES:
        return existing, ["Photo count exceeds the ten-image catalogue limit"]
    if not files or len(existing) >= len(files):
        return existing, []
    # Re-upload the full ordered set to deterministic public IDs. overwrite=True makes
    # partial retries safe and avoids treating one successful later photo as an earlier file.
    urls, issues = [], []
    for index, item in enumerate(files, start=1):
        try:
            blob = _download_image(_file_url(item))
            uploaded = upload_property_images(cloudinary, listing_id, [blob], start_index=index)
            urls.extend(x.url for x in uploaded)
        except Exception as exc:
            issues.append(f"Photo {index} upload failed: {str(exc)[:220]}")
    # Only publish a complete ordered photo set. On partial failure, deterministic
    # Cloudinary IDs allow a later retry to overwrite the same files safely.
    return (urls if not issues else existing), issues


def _native_photo_ids(notion, photos: list, listing_id: str, existing_listing, *, fresh_upload: bool):
    """Notion-hosted copies of the intake photos for the Housing "Photos" column.

    Runs when this intake run uploaded a fresh photo set, or when the Housing page has
    no native photos yet. A text-only edit on a page that already has its photos leaves
    the column untouched. Returns (upload ids, issues); an empty list means no change.
    """
    if not photos or len(photos) > MAX_IMAGES:
        return [], []
    has_native = bool(existing_listing and ((existing_listing.get("properties") or {}).get("Photos") or {}).get("files"))
    if has_native and not fresh_upload:
        return [], []
    ids, issues = [], []
    for index, item in enumerate(photos, start=1):
        try:
            blob = _download_image(_file_url(item))
            kind = "image/png" if blob[:8] == b"\x89PNG\r\n\x1a\n" else "image/webp" if blob[8:12] == b"WEBP" else "image/jpeg"
            ids.append(notion.upload_file(blob, f"{listing_id}-{index:02d}.jpg", kind))
        except Exception as exc:
            issues.append(f"Native photo {index} upload failed: {str(exc)[:200]}")
    return ([] if issues else ids), issues


def _aws_secret_value(environment_name: str) -> str:
    """Load the current runtime credential from Secrets Manager, never Lambda env plaintext."""
    import boto3
    arn = os.environ.get(environment_name, "").strip()
    if not arn:
        raise IntakeError(f"{environment_name} is not configured")
    value = boto3.client("secretsmanager").get_secret_value(SecretId=arn).get("SecretString", "")
    if not value:
        raise IntakeError(f"{environment_name} secret is empty")
    return str(value)


def _runtime_cloudinary_client() -> CloudinaryClient:
    try:
        values = json.loads(_aws_secret_value("CLOUDINARY_SECRET_ARN"))
    except json.JSONDecodeError as exc:
        raise IntakeError("Cloudinary secret is not valid JSON") from exc
    required = ("cloud_name", "api_key", "api_secret")
    if not isinstance(values, dict) or any(not str(values.get(key) or "").strip() for key in required):
        raise IntakeError("Cloudinary secret is missing required credential fields")
    return CloudinaryClient(credentials=CloudinaryCredentials(**{key: str(values[key]) for key in required}))


def _runtime_maps_client() -> OlaInventoryMaps:
    # No Google credentials or API fallback. Source links are links only.
    return OlaInventoryMaps(ola_client=_runtime_ola_client())


def _runtime_ola_client() -> OlaMapsClient:
    # Optional enrichment: a missing key must never block raw intake. With no
    # key configured, locality normalization still runs on text similarity and
    # simply skips the Ola lookup.
    return OlaMapsClient()


def _option_names(definition: dict) -> set[str]:
    select = definition.get("select") or definition.get("multi_select") or {}
    return {str(option.get("name") or "") for option in (select.get("options") or []) if str(option.get("name") or "")}


def enforce_select_vocabulary(schema: dict, properties: dict) -> None:
    """Dropdown fields only ever take an existing option - data never creates options.

    A value outside the live vocabulary stops the write instead of letting Notion
    auto-create a new dropdown option; the intake marks the listing Needs Review.
    """
    for name, payload in (properties or {}).items():
        definition = (schema or {}).get(name) or {}
        property_type = definition.get("type")
        if property_type == "select":
            value = str(((payload.get("select") or {}) or {}).get("name") or "")
            if not value:
                continue
            options = _option_names(definition)
            if options and value not in options:
                raise IntakeError(f"{name}: '{value}' is not an existing dropdown option; refusing to create a new one")
        elif property_type == "multi_select":
            values = [str(item.get("name") or "") for item in (payload.get("multi_select") or []) if str(item.get("name") or "")]
            options = _option_names(definition)
            unknown = [value for value in values if options and value not in options]
            if unknown:
                raise IntakeError(f"{name}: {unknown} not existing dropdown options; refusing to create new ones")


def _locality_select_options(listing_schema: dict) -> list[str]:
    definition = (listing_schema or {}).get("locality") or {}
    select = definition.get("select") or {}
    return [
        str(option.get("name") or "").strip()
        for option in (select.get("options") or [])
        if str(option.get("name") or "").strip()
    ]


def process_page(
    page_id: str,
    *,
    event_type: str = "",
    updated_property_ids: list[str] | None = None,
    notion: NotionClient | None = None,
    store: SupabaseIntakeStore | None = None,
    cloudinary: CloudinaryClient | None = None,
    maps_client=None,
    ola_client=None,
):
    notion = notion or NotionClient(_notion_secret_value("api_token"))
    store = store or SupabaseIntakeStore()
    if event_type == "page.deleted":
        existing = store.find_inventory(page_id)
        if existing.get("found"):
            store.delete_inventory(page_id)
            store.finish(page_id, "processed", listing_page_id=page_id, note="Deleted from canonical Notion Housing Listings.")
            return {"status": "deleted", "listing_id": existing.get("listing_id", "")}
        return {"status": "ignored", "listing_id": ""}
    page = notion.get_page(page_id)
    if page.get("archived") or page.get("in_trash"):
        store.finish(page_id, "processed", note="Source intake page is deleted; stale delivery ignored.")
        _log_event("intake_deleted_source_ignored", page_id=page_id, event_type=event_type)
        return {"status": "ignored", "listing_id": "", "reason": "source_page_deleted"}
    parent = page.get("parent") or {}
    parent_database_id = str(parent.get("database_id") or parent.get("data_source_id") or "").replace("-", "").lower()
    if parent_database_id == CATALOGUE_PANEL_DATABASE_ID:
        props = page.get("properties") or {}
        title = "".join(str(x.get("plain_text") or "") for x in ((props.get("Name") or {}).get("title") or []))
        operation = title.strip().lower()
        run_ticked = bool((props.get("Run") or {}).get("checkbox"))
        import catalogue_trigger
        if run_ticked and operation in catalogue_trigger.OPERATIONS:
            _log_event("catalogue_panel_triggered", operation=operation, page_id=page_id)
            return {"status": "panel_trigger", "operation": operation, "listing_id": ""}
        return {"status": "ignored", "listing_id": ""}
    if parent_database_id == LISTINGS_DATABASE_ID:
        # Retired 24 Nov 2026 (Zeid): the "Post to Catalogue" tick branch is
        # gone - Housing-row edits always take the idempotent listing sync.
        return process_listing_page(page, notion=notion, store=store)
    if parent_database_id != INTAKE_DATABASE_ID:
        if event_type in {"page.moved", "page.undeleted"} and store.find_inventory(page_id).get("found"):
            return process_listing_page(page, notion=notion, store=store, force_deleted=True)
        return {"status": "ignored", "listing_id": ""}

    props = page.get("properties") or {}
    if event_type == "page.properties_updated":
        changed_ids = {str(value).strip() for value in (updated_property_ids or []) if str(value).strip()}
        intake_input_ids = {
            str((props.get(name) or {}).get("id") or "").strip()
            for name in ("Raw Property Data", "Photos")
        }
        intake_input_ids.discard("")
        if not changed_ids.intersection(intake_input_ids):
            _log_event("intake_property_update_ignored", page_id=page_id, updated_property_count=len(changed_ids))
            return {"status": "ignored", "listing_id": ""}

    cloudinary = cloudinary or _runtime_cloudinary_client()
    raw_text = _plain_text(props.get("Raw Property Data") or {})
    if not raw_text:
        note = "Raw Property Data is required before processing."
        combined_notes = _append_processing_notes(notion, page_id, note)
        notion.update_page(page_id, {
            "Intake Status": {"status": {"name": "Needs Review"}},
            "Processing Notes": _rich(combined_notes),
        })
        return {"status": "Needs Review", "listing_id": "", "issues": [note]}
    photos = _photos(page)
    photo_signature = [
        {"type": x.get("type"), "name": x.get("name"), "path": urlparse(_file_url(x)).path}
        for x in photos
    ]
    payload_hash = hashlib.sha256(json.dumps({"raw": raw_text, "photos": photo_signature}, sort_keys=True).encode()).hexdigest()
    claim, item = store.claim(page_id, payload_hash)
    if claim == "duplicate":
        return {"status": "already_processed", "listing_id": item.get("listing_id", "")}
    if claim == "in_progress":
        return {"status": "processing", "listing_id": item.get("listing_id", "")}

    listing_id = str((item or {}).get("listing_id") or _plain_text(props.get("Listing ID") or {})).strip()
    try:
        # Validate the canonical Notion contract before media uploads or page creation.
        notion.validate_listing_schema()
        if not listing_id:
            listing_id = store.allocate_listing_id(page_id)
            store.set_listing_id(page_id, listing_id)
        notion.update_page(page_id, {"Intake Status": {"status": {"name": "Processing"}}, "Listing ID": _rich(listing_id)})
        existing_listing = notion.find_listing(listing_id)
        row = pipeline.initial_row(listing_id, raw_text, str(page.get("created_time") or datetime.now(timezone.utc).isoformat())[:10])
        previous = listing_snapshot(existing_listing) if existing_listing else None
        if previous:
            # The legacy parser remains a pure 48-field extraction boundary. Do not
            # feed canonical lifecycle/metadata into it, or legacy status into routing.
            row.update({k: v for k, v in previous.items() if k in schema.NAMES
                        and k not in notion_lifecycle.LEGACY_STATUS_FIELDS})
            row["listing_id"] = listing_id
            row["raw_message_text"] = raw_text
        protected = {k: row.get(k, "") for k in ("meta_catalog_id", "posted_url", "posted_at", "error_notes")}
        for key in protected:
            row[key] = ""

        previous_urls = row.get("cloudinary_image_urls")
        urls, photo_issues = _upload_photos(page, listing_id, row, cloudinary)
        if urls:
            row["cloudinary_image_urls"] = catalog_urls([Upload(url=u, public_id="", index=i) for i, u in enumerate(urls, start=1)])
        processed, issues = pipeline.process_closed_session(raw_text, row=row, maps_client=maps_client or _runtime_maps_client())
        issues.extend(photo_issues)
        if photo_issues:
            processed["status"] = "Needs Review"
        # Owner rule (15 Nov 2026): raw Location text is normalized to the
        # closest locality dropdown option instead of failing the listing.
        listing_schema = getattr(notion, "_listing_schema", None) or notion.validate_listing_schema()
        locality_options = _locality_select_options(listing_schema)
        raw_locality = str(processed.get("locality") or "").strip()
        if locality_options and raw_locality and raw_locality not in locality_options:
            normalization = normalize_locality(
                raw_locality,
                locality_options,
                ola_client=ola_client or _runtime_ola_client(),
                context=(processed.get("landmark", ""), processed.get("society_name", "")),
            )
            if normalization.canonical:
                processed["locality"] = normalization.canonical
                if normalization.note:
                    issues.append(normalization.note)
            else:
                processed["locality"] = ""
                processed["status"] = "Needs Review"
                issues.append(
                    f"Location '{raw_locality}' is not in the locality list and no close option matched "
                    "(checked the list and Ola Maps). Pick the right locality from the dropdown; "
                    "the original Location stays in Raw Property Data."
                )
        area_note = area_extract.unsupported_area_note(raw_text, processed)
        if area_note:
            issues.append(area_note)
            processed["status"] = "Needs Review"
        # Dropdown locality wins everywhere (owner rule, 21 Nov): rebuild the
        # card title AFTER locality normalization so the canonical value lands.
        processed["catalog_title"] = build_catalog_title(processed)
        processed["cloudinary_image_urls"] = row.get("cloudinary_image_urls", processed.get("cloudinary_image_urls", ""))
        maps_url = str(processed.get("google_maps_url") or "").strip()
        caption_maps_url = str(processed.pop("_caption_maps_url", "") or "").strip()
        ola_checked = any(issue.startswith("Ola background checks:") for issue in issues)
        maps_failed = bool(maps_url) and (ola_checked or any(issue.startswith(("Google Maps verification failed", "Google Maps API unavailable", "Background Maps check unavailable")) for issue in issues))
        maps_api_unavailable = bool(maps_url) and (ola_checked or any(issue.startswith(("Google Maps API unavailable", "Background Maps check unavailable")) for issue in issues))
        if maps_url and not _short_mobile_maps_url(maps_url) and not caption_maps_url:
            issues.append("Original Maps URL is not a supported short mobile link; omitted from the caption and requires review.")
            processed["status"] = "Needs Review"
        verified_society = next((issue.split(":", 1)[1].strip() for issue in issues if issue.startswith("Google Maps verified place name:")), "")
        caption = build_whatsapp_post(processed, raw_text, maps_verified=not maps_failed, verified_society_name=verified_society, allow_unverified_source_map=maps_api_unavailable, resolved_maps_url=caption_maps_url)
        if not caption:
            issues.append("WhatsApp caption not generated because a verified locality or Maps verification is missing.")
            processed["status"] = "Needs Review"
        processed["whatsapp_post"] = caption  # legacy compatibility field
        group_issues = []
        processed["whatsapp_group_description"] = build_whatsapp_group_description(
            processed, raw_text, verified_society_name=verified_society,
            # A URL alone is not proof of verification. The pipeline's
            # caption_maps_url is populated only when the Maps check produced
            # an accepted source link; otherwise the formatter uses Raw
            # Property Data as the explicitly requested fallback.
            maps_verified=bool(caption_maps_url) and not maps_failed, issues=group_issues,
        )
        if group_issues:
            issues.extend(group_issues)
            # A temporary Maps API outage is not a source-data conflict. Keep
            # the intake's existing status when the original Raw Property
            # Data URL has been retained as the explicitly requested fallback.
            if not maps_api_unavailable:
                processed["status"] = "Needs Review"
        # Preserve the existing Catalogue formatter output exactly.
        catalogue_text = build_catalogue_description(
            processed, raw_text,
            verified_society_name=verified_society,
        )
        processed["catalogue_description"] = catalogue_text  # legacy compatibility field
        processed["whatsapp_catalogue_description"] = catalogue_text
        processed["facebook_marketplace_description"] = build_facebook_marketplace_description(
            processed, raw_text,
        )
        final_state = "Needs Review" if processed.get("status") == "Needs Review" else "Processed"
        lifecycle = notion_lifecycle.finish_processing(processed, previous)
        processed.update(protected)
        # No old Housing lifecycle keys enter the persistence payload.
        processed = {k: v for k, v in processed.items() if k not in notion_lifecycle.LEGACY_STATUS_FIELDS}
        processed.update(lifecycle)
        native_ids, native_issues = _native_photo_ids(
            notion, photos, listing_id, existing_listing,
            fresh_upload=bool(urls) and urls != [x.strip() for x in str(previous_urls or "").split(",") if x.strip()],
        )
        if native_ids:
            processed["_native_photo_upload_ids"] = native_ids
        if native_issues:
            issues.extend(native_issues)
            final_state = "Needs Review"
        listing_page_id = notion.save_listing(processed)
        note = "; ".join(issues) if issues else "Processed through the canonical EFPS inventory pipeline."
        combined_notes = _append_processing_notes(notion, page_id, note)
        notion.update_page(page_id, {
            "Intake Status": {"status": {"name": final_state}},
            "Listing ID": _rich(listing_id),
            "Processing Notes": _rich(combined_notes),
            "Processed At": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
            "Processed Property": {"relation": [{"id": listing_page_id}]},
        })
        store.finish(page_id, "needs_review" if final_state == "Needs Review" else "processed", listing_page_id=listing_page_id, note=note)
        return {"status": final_state, "listing_id": listing_id, "listing_page_id": listing_page_id, "issues": issues}
    except Exception as exc:
        note = f"Processing failed: {str(exc)[:1500]}"
        # A source page can be deleted while an asynchronous duplicate delivery is
        # still running. Treat a confirmed missing page as a terminal ignored event.
        try:
            current_page = notion.get_page(page_id)
            if current_page.get("archived") or current_page.get("in_trash"):
                store.finish(page_id, "processed", note="Source intake page was deleted during processing; no further update is required.")
                _log_event("intake_source_deleted_during_processing", page_id=page_id, listing_id=listing_id)
                return {"status": "ignored", "listing_id": listing_id, "reason": "source_page_deleted"}
        except Exception as lookup_error:
            lookup_text = str(lookup_error).lower()
            if "object_not_found" in lookup_text or "failed (404)" in lookup_text:
                store.finish(page_id, "processed", note="Source intake page no longer exists; stale delivery ignored.")
                _log_event("intake_source_missing_during_processing", page_id=page_id, listing_id=listing_id)
                return {"status": "ignored", "listing_id": listing_id, "reason": "source_page_missing"}
        try:
            combined_notes = _append_processing_notes(notion, page_id, note)
            notion.update_page(page_id, {"Intake Status": {"status": {"name": "Needs Review"}}, "Listing ID": _rich(listing_id), "Processing Notes": _rich(combined_notes)})
        except Exception as status_error:
            _log_event("intake_failure_status_update_failed", page_id=page_id, listing_id=listing_id,
                       original_error_type=type(exc).__name__, status_error_type=type(status_error).__name__,
                       status_error=str(status_error)[:500])
        store.finish(page_id, "failed", note=note)
        raise


def process_listing_page(page: dict, *, notion: NotionClient, store: SupabaseIntakeStore, force_deleted: bool = False):
    """Mirror a Housing Listings page directly into the inventory used by the dashboard."""
    page_id = str(page.get("id") or "").strip()
    if not re.fullmatch(r"[0-9a-fA-F-]{32,36}", page_id):
        raise IntakeError("Invalid Housing Listings page ID")
    row = listing_snapshot(page)
    deleted = force_deleted or bool(page.get("archived") or page.get("in_trash"))
    payload_hash = hashlib.sha256(json.dumps({"row": row, "deleted": deleted}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    claim, item = store.claim(page_id, payload_hash)
    if claim == "duplicate":
        existing = store.find_inventory(page_id)
        if existing.get("found") and not existing.get("deleted_at"):
            existing_listing_id = str(existing.get("listing_id") or item.get("listing_id") or "").strip()
            if existing_listing_id:
                store.set_listing_id(page_id, existing_listing_id)
            return {"status": "already_processed", "listing_id": existing_listing_id}
        # A completed intake record without its inventory projection can occur
        # after a partial deployment or projection failure. Rebuild the same
        # row from Notion so an idempotent backfill also repairs that gap.
    if claim == "in_progress":
        return {"status": "processing", "listing_id": item.get("listing_id", "")}

    listing_id = row["listing_id"].strip() or str((item or {}).get("listing_id") or "").strip()
    try:
        if deleted and not listing_id:
            store.delete_inventory(page_id)
            store.finish(page_id, "processed", listing_page_id=page_id, note="Archived from canonical Notion Housing Listings.")
            return {"status": "deleted", "listing_id": ""}
        if not listing_id:
            existing = store.find_inventory(page_id)
            listing_id = str(existing.get("listing_id") or "").strip()
        if not listing_id:
            listing_id = store.allocate_listing_id(page_id)
        if row["listing_id"].strip() != listing_id:
            notion.update_page(page_id, {"listing_id": _rich(listing_id)})
        row["listing_id"] = listing_id
        store.set_listing_id(page_id, listing_id)
        if not deleted:
            # Stamped 21 Nov: every Housing row edit refreshes the catalogue
            # description. Deterministic rebuild; written only when it changed,
            # which keeps the webhook loop finite (next event sees equality).
            # The Maps link in the description is always the owner's exact
            # input link (google_maps_url); nothing is carried over.
            if str(row.get("locality") or "").strip():
                title = build_catalog_title(row)
                if title != str(row.get("catalog_title") or ""):
                    notion.update_page(page_id, {"catalog_title": _rich(title), "Property": {"title": [{"text": {"content": title}}]}})
                    row["catalog_title"] = title
                raw_text = str(row.get("raw_message_text") or "")
                existing_group = str(row.get("whatsapp_group_description") or row.get("whatsapp_post") or "")
                raw_urls = re.findall(r"https?://[^\s<>]+", raw_text, flags=re.I)
                short_link = next((url.rstrip(".,);]") for url in raw_urls
                                   if _short_mobile_maps_url(url.rstrip(".,);]"))), "")
                # An edit is not a fresh Maps verification. Reuse the existing
                # verified map label only when the prior caption already carried
                # a map label and the original short URL is still in raw intake.
                prior_label = re.search(r"\*📍\s*([^*]+):\*\s*\n(https://[^\s]+)", existing_group)
                prior_map_verified = bool(short_link and prior_label)
                verified_label = prior_label.group(1).strip() if prior_map_verified else ""
                if verified_label.casefold() == str(row.get("locality") or "").strip().casefold():
                    verified_label = ""
                group_issues = []
                group_text = build_whatsapp_group_description(
                    row, raw_text, verified_society_name=verified_label,
                    maps_verified=prior_map_verified, issues=group_issues,
                )
                if group_text and group_text != str(row.get("whatsapp_group_description") or ""):
                    notion.update_page(page_id, {"whatsapp_group_description": _rich(group_text)})
                    row["whatsapp_group_description"] = group_text
                if group_text and group_text != str(row.get("whatsapp_post") or ""):
                    notion.update_page(page_id, {"whatsapp_post": _rich(group_text)})
                    row["whatsapp_post"] = group_text
                if group_issues:
                    _log_event("description_review_required", listing_id=listing_id, issues=group_issues)
            raw_text = str(row.get("raw_message_text") or "")
            existing_desc = str(row.get("whatsapp_catalogue_description") or row.get("catalogue_description") or "")
            rebuilt = build_catalogue_description(row, raw_text)
            if rebuilt and rebuilt != existing_desc.strip():
                notion.update_page(page_id, {
                    "whatsapp_catalogue_description": _rich(rebuilt),
                    "catalogue_description": _rich(rebuilt),
                })
                row["whatsapp_catalogue_description"] = rebuilt
                row["catalogue_description"] = rebuilt
            facebook_text = build_facebook_marketplace_description(row, raw_text)
            if facebook_text and facebook_text != str(row.get("facebook_marketplace_description") or ""):
                notion.update_page(page_id, {"facebook_marketplace_description": _rich(facebook_text)})
                row["facebook_marketplace_description"] = facebook_text
        store.sync_inventory(page_id, row, deleted=deleted)
        note = "Synced from canonical Notion Housing Listings."
        store.finish(page_id, "processed", listing_page_id=page_id, note=note)
        return {"status": "deleted" if deleted else "synced", "listing_id": listing_id}
    except Exception as exc:
        store.finish(page_id, "failed", listing_page_id=page_id, note=f"Notion inventory sync failed: {str(exc)[:1500]}")
        raise


def _enqueue_worker(
    page_id: str,
    function_arn: str,
    *,
    event_type: str = "",
    event_id: str = "",
    event_row_id: str = "",
    attempt_number: int | None = None,
    updated_property_ids: list[str] | None = None,
):
    import boto3
    response = boto3.client("lambda").invoke(
        FunctionName=function_arn,
        InvocationType="Event",
        Payload=json.dumps({
            "_efps_notion_worker": True,
            "page_id": page_id,
            "event_type": event_type,
            "event_id": event_id,
            "event_row_id": event_row_id,
            "attempt_number": attempt_number,
            "updated_property_ids": updated_property_ids or [],
        }).encode("utf-8"),
    )
    if int(response.get("StatusCode") or 0) != 202:
        raise IntakeError("Notion intake worker enqueue was not accepted")


def _enqueue_catalogue_trigger(operation: str, function_arn: str):
    import boto3
    response = boto3.client("lambda").invoke(
        FunctionName=function_arn,
        InvocationType="Event",
        Payload=json.dumps({"_efps_catalogue_trigger": True, "operation": operation}).encode("utf-8"),
    )
    if int(response.get("StatusCode") or 0) != 202:
        raise IntakeError("Catalogue trigger enqueue was not accepted")


NOTION_PAGE_EVENT_TYPES = {
    "page.created", "page.properties_updated", "page.content_updated", "page.moved",
    "page.deleted", "page.undeleted", "page.locked", "page.unlocked", "page.updated",
}
_UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.I)
_SENSITIVE_EVENT_KEY = re.compile(r"token|secret|password|authorization|api[_-]?key|cookie", re.I)


def _is_uuid(value: object) -> bool:
    return isinstance(value, str) and bool(_UUID_PATTERN.fullmatch(value.strip()))


def _safe_event_value(value):
    """Preserve event data while removing credential-like values before database storage."""
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if _SENSITIVE_EVENT_KEY.search(str(key)) else _safe_event_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_safe_event_value(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _event_record_input(payload: dict, raw_body: str, *, malformed: bool = False) -> dict:
    payload_sha256 = hashlib.sha256(raw_body.encode("utf-8")).hexdigest()
    event_id = str(payload.get("id") or payload.get("event_id") or "").strip()
    notion_event_id = event_id.lower() if _is_uuid(event_id) else None
    if notion_event_id:
        event_key = f"event:{notion_event_id}"
    else:
        stable_payload = dict(payload)
        stable_payload.pop("attempt_number", None)
        stable_fingerprint = hashlib.sha256(json.dumps(stable_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        event_key = f"sha256:{stable_fingerprint}"
    entity = payload.get("entity") if isinstance(payload.get("entity"), dict) else {}
    entity_id = str(entity.get("id") or "").strip()
    event_type = str(payload.get("type") or payload.get("event_type") or "unknown").strip()[:200] or "unknown"
    entity_type = str(entity.get("type") or "").strip()[:80]
    page_id = entity_id.lower() if event_type in NOTION_PAGE_EVENT_TYPES and entity_type == "page" and _is_uuid(entity_id) else None
    attempt = payload.get("attempt_number")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or not 1 <= attempt <= 8:
        attempt = None
    event_timestamp = payload.get("timestamp")
    if not isinstance(event_timestamp, str):
        event_timestamp = None
    if malformed:
        safe_payload = {
            "malformed_json": True,
            "raw_body_sha256": payload_sha256,
            "raw_body_size": len(raw_body.encode("utf-8")),
        }
    else:
        safe_payload = _safe_event_value(payload)
    return {
        "event_key": event_key,
        "notion_event_id": notion_event_id,
        "event_type": event_type,
        "workspace_id": payload.get("workspace_id") if _is_uuid(payload.get("workspace_id")) else None,
        "subscription_id": payload.get("subscription_id") if _is_uuid(payload.get("subscription_id")) else None,
        "integration_id": payload.get("integration_id") if _is_uuid(payload.get("integration_id")) else None,
        "entity_type": entity_type or None,
        "entity_id": entity_id.lower() if _is_uuid(entity_id) else None,
        "page_id": page_id,
        "event_timestamp": event_timestamp,
        "attempt_number": attempt,
        "payload": safe_payload if isinstance(safe_payload, dict) else {"payload": safe_payload},
        "payload_sha256": payload_sha256,
    }


def _enqueue_listing_backfill(function_arn: str, *, notion=None, store=None, lambda_client=None):
    """Reconcile active Notion rows, enqueue only changed/restored pages, and tombstone missing pages."""
    notion = notion or NotionClient(_notion_secret_value("api_token"))
    store = store or SupabaseIntakeStore()
    pages = notion.list_listings()
    if not pages:
        raise IntakeError("Notion Housing Listings reconciliation returned zero pages; refusing mass tombstone")
    import boto3
    client = lambda_client or boto3.client("lambda")
    active_page_ids, active_listings, accepted, skipped = [], [], 0, 0
    for page in pages:
        page_id = str(page.get("id") or "").strip()
        if not re.fullmatch(r"[0-9a-fA-F-]{32,36}", page_id):
            raise IntakeError("Notion reconciliation returned an invalid page ID")
        active_page_ids.append(page_id)
        row = listing_snapshot(page)
        existing = store.find_inventory(page_id)
        if not row["listing_id"].strip() and existing.get("listing_id"):
            row["listing_id"] = str(existing["listing_id"])
        if row["listing_id"].strip():
            active_listings.append({"page_id": page_id, "listing_id": row["listing_id"].strip()})
        source_hash = hashlib.sha256(json.dumps(row, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        unchanged = bool(existing.get("found")) and not existing.get("deleted_at") and existing.get("source_hash") == source_hash
        if unchanged:
            skipped += 1
            continue
        response = client.invoke(
            FunctionName=function_arn,
            InvocationType="Event",
            Payload=json.dumps({"_efps_notion_worker": True, "page_id": page_id, "event_type": "reconciliation"}).encode("utf-8"),
        )
        if int(response.get("StatusCode") or 0) != 202:
            raise IntakeError("Notion inventory reconciliation worker enqueue was not accepted")
        accepted += 1
    tombstones = store.reconcile_pages(active_page_ids, active_listings)
    result = {"checked": len(active_page_ids), "accepted": accepted, "skipped_unchanged": skipped,
              "listing_ids_reconciled": int(tombstones.get("listing_ids_reconciled") or 0),
              "soft_deleted_missing": int(tombstones.get("soft_deleted") or 0)}
    _log_event("reconciliation_enqueued", **result)
    return result


def _notion_secret_value(key: str, *, update_webhook_token: str = "") -> str:
    """Read Notion credentials at runtime; never expose the API token in Lambda environment config."""
    import boto3
    secret_arn = os.environ.get("NOTION_SECRET_ARN", "")
    if not secret_arn:
        raise IntakeError("NOTION_SECRET_ARN is not configured")
    client = boto3.client("secretsmanager")
    current = json.loads(client.get_secret_value(SecretId=secret_arn)["SecretString"])
    if update_webhook_token:
        current["webhook_secret"] = update_webhook_token
        client.put_secret_value(SecretId=secret_arn, SecretString=json.dumps(current))
        return update_webhook_token if key == "webhook_secret" else str(current.get(key) or "")
    return str(current.get(key) or "")


def _notion_webhook_secret(*, update_token: str = "") -> str:
    """Read the Notion webhook verification token; persist it on first subscription handshake."""
    return _notion_secret_value("webhook_secret", update_webhook_token=update_token)


def _record_unverified_delivery(raw_body: str, reason: str, context, request_event: dict | None = None) -> bool:
    """Audit rejected deliveries without storing their body; retain safe gateway origin metadata."""
    digest = hashlib.sha256(raw_body.encode("utf-8")).hexdigest()
    payload = {
        "unverified_delivery": True,
        "reason": reason,
        "raw_body_sha256": digest,
        "raw_body_size": len(raw_body.encode("utf-8")),
    }
    request_context = (request_event or {}).get("requestContext") or {}
    identity = request_context.get("identity") or {}
    http = request_context.get("http") or {}
    payload["request_origin"] = {
        "source_ip": identity.get("sourceIp") or http.get("sourceIp"),
        "user_agent": identity.get("userAgent") or http.get("userAgent"),
        "gateway_request_id": request_context.get("requestId"),
        "stage": request_context.get("stage"),
    }
    record = _event_record_input(payload, raw_body)
    record["event_key"] = f"sha256:unverified:{digest}"
    record["payload"] = payload
    store = SupabaseIntakeStore()
    result = store.record_webhook_event(**record)
    row_id = str(result.get("id") or "")
    if not row_id.startswith("notion-webhook:"):
        raise IntakeError("Supabase returned no Notion event record ID")
    if result.get("should_enqueue"):
        store.update_webhook_event(
            row_id,
            "rejected",
            aws_request_id=getattr(context, "aws_request_id", ""),
            error=f"Webhook authentication failed: {reason}.",
            outcome={"validation": "rejected", "reason": reason},
        )
    return True


def lambda_handler(event, context):
    if event.get("_efps_catalogue_schedule"):
        # Tuesday 9 AM IST scheduled cleanup + daily watchdog (approved 21 Nov).
        import catalogue_scheduler
        return catalogue_scheduler.handle_schedule(
            event, context, notion_token=_notion_secret_value("api_token"))
    if event.get("_efps_catalogue_trigger"):
        operation = str(event.get("operation") or "").strip().lower()
        started = time.monotonic()
        try:
            import catalogue_trigger
            result = catalogue_trigger.run_catalogue_operation(operation, notion_token=_notion_secret_value("api_token"))
            _log_event("catalogue_operation_completed", operation=operation,
                       aws_request_id=getattr(context, "aws_request_id", ""),
                       duration_ms=round((time.monotonic() - started) * 1000),
                       counts=result.get("counts") or {}, dry_run=bool(result.get("dry_run")))
            return {"status": "completed", "operation": operation, **result}
        except Exception as exc:
            _log_event("catalogue_operation_failed", operation=operation,
                       aws_request_id=getattr(context, "aws_request_id", ""),
                       error_type=type(exc).__name__, error=str(exc)[:800],
                       duration_ms=round((time.monotonic() - started) * 1000))
            raise
    if event.get("_efps_notion_backfill"):
        started = time.monotonic()
        try:
            result = _enqueue_listing_backfill(context.invoked_function_arn)
            _log_event("reconciliation_completed", aws_request_id=getattr(context, "aws_request_id", ""), duration_ms=round((time.monotonic() - started) * 1000), **result)
            return result
        except Exception as exc:
            _log_event("reconciliation_failed", aws_request_id=getattr(context, "aws_request_id", ""), error_type=type(exc).__name__, error=str(exc)[:800])
            raise
    # Internal asynchronous invocation: raise on failure so Lambda retry policy applies.
    if event.get("_efps_notion_worker"):
        page_id = str(event.get("page_id") or "").strip()
        event_type = str(event.get("event_type") or "")
        event_id = str(event.get("event_id") or "")
        event_row_id = str(event.get("event_row_id") or "").strip()
        updated_property_ids = event.get("updated_property_ids") or []
        if not re.fullmatch(r"[0-9a-fA-F-]{32,36}", page_id):
            raise IntakeError("Invalid asynchronous intake page ID")
        started = time.monotonic()
        event_store = SupabaseIntakeStore() if event_row_id else None
        if event_store:
            start_result = event_store.update_webhook_event(
                event_row_id,
                "processing",
                aws_request_id=getattr(context, "aws_request_id", ""),
                page_id=page_id,
            )
            if start_result.get("status") in {"processed", "needs_review", "rejected", "unsupported", "ignored"}:
                return {"status": "already_processed", "event_id": event_id, "event_row_id": event_row_id}
        _log_event("worker_started", page_id=page_id, event_type=event_type, event_id=event_id, aws_request_id=getattr(context, "aws_request_id", ""))
        try:
            result = process_page(page_id, event_type=event_type, updated_property_ids=updated_property_ids)
            if str(result.get("status") or "") in {"panel_trigger"}:
                _enqueue_catalogue_trigger(str(result.get("operation") or ""), context.invoked_function_arn)
                result = {**result, "status": "queued", "enqueued": str(result.get("operation") or "")}
        except Exception as exc:
            if _is_missing_notion_page_error(exc):
                if event_store:
                    event_store.update_webhook_event(
                        event_row_id,
                        "ignored",
                        aws_request_id=getattr(context, "aws_request_id", ""),
                        outcome={"status": "ignored", "reason": "source_page_missing"},
                        page_id=page_id,
                    )
                _log_event("worker_completed", page_id=page_id, event_type=event_type, event_id=event_id,
                           aws_request_id=getattr(context, "aws_request_id", ""), status="ignored",
                           reason="source_page_missing", duration_ms=round((time.monotonic() - started) * 1000))
                return {"status": "ignored", "listing_id": "", "reason": "source_page_missing"}
            if event_store:
                try:
                    event_store.update_webhook_event(
                        event_row_id,
                        "failed",
                        aws_request_id=getattr(context, "aws_request_id", ""),
                        error=f"{type(exc).__name__}: {str(exc)[:1500]}",
                        outcome={"exception_type": type(exc).__name__},
                        page_id=page_id,
                    )
                except Exception as ledger_exc:
                    _log_event("event_history_update_failed", event_row_id=event_row_id, error_type=type(ledger_exc).__name__)
            _log_event("worker_failed", page_id=page_id, event_type=event_type, event_id=event_id,
                       aws_request_id=getattr(context, "aws_request_id", ""), error_type=type(exc).__name__, error=str(exc)[:1000],
                       duration_ms=round((time.monotonic() - started) * 1000))
            raise
        worker_status = str(result.get("status") or "unknown")
        if worker_status.lower() in {"processing", "in_progress"}:
            retry_error = "Inventory page is already being processed; retry this event after the active page claim finishes."
            if event_store:
                event_store.update_webhook_event(
                    event_row_id,
                    "failed",
                    aws_request_id=getattr(context, "aws_request_id", ""),
                    error=retry_error,
                    outcome={"status": worker_status},
                    page_id=page_id,
                )
            raise IntakeError(retry_error)
        if worker_status.lower() == "needs review":
            terminal_status = "needs_review"
        elif worker_status.lower() == "ignored":
            terminal_status = "ignored"
        else:
            terminal_status = "processed"
        if event_store:
            event_store.update_webhook_event(
                event_row_id,
                terminal_status,
                aws_request_id=getattr(context, "aws_request_id", ""),
                outcome=result,
                page_id=page_id,
                listing_id=str(result.get("listing_id") or ""),
                listing_page_id=str(result.get("listing_page_id") or (page_id if event_type in NOTION_PAGE_EVENT_TYPES else "")),
            )
        _log_event("worker_completed", page_id=page_id, event_type=event_type, event_id=event_id,
                   aws_request_id=getattr(context, "aws_request_id", ""), status=result.get("status", "unknown"),
                   listing_id=result.get("listing_id", ""), duration_ms=round((time.monotonic() - started) * 1000))
        return result

    headers = {str(k).lower(): str(v) for k, v in (event.get("headers") or {}).items()}
    raw_body = event.get("body") or "{}"

    # Operator trigger route: HMAC-signed, enqueues the gated catalogue operation.
    http_ctx = (event.get("requestContext") or {}).get("http") or {}
    route_path = str(event.get("rawPath") or http_ctx.get("path") or event.get("path") or "")
    if route_path.rstrip("/").endswith("/catalogue/run"):
        try:
            secret = _aws_secret_value("CATALOGUE_TRIGGER_SECRET_ARN")
        except Exception as exc:
            _log_event("catalogue_trigger_unavailable", error_type=type(exc).__name__)
            return {"statusCode": 503, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"error": "catalogue trigger is not configured"})}
        import catalogue_trigger
        if not catalogue_trigger.verify_signature(headers, secret=secret):
            _log_event("catalogue_trigger_rejected", reason="invalid_signature")
            return {"statusCode": 401, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"error": "invalid signature"})}
        try:
            operation = catalogue_trigger.parse_operation(raw_body)
        except catalogue_trigger.CatalogueTriggerError as exc:
            return {"statusCode": 400, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"error": str(exc)[:300]})}
        _enqueue_catalogue_trigger(operation, context.invoked_function_arn)
        _log_event("catalogue_trigger_accepted", operation=operation)
        return {"statusCode": 202, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"ok": True, "operation": operation})}
    if event.get("isBase64Encoded"):
        import base64
        raw_body = base64.b64decode(raw_body).decode("utf-8")
    try:
        payload = json.loads(raw_body)
        payload_is_json = True
    except (json.JSONDecodeError, TypeError, UnicodeDecodeError):
        payload = None
        payload_is_json = False

    # Notion's one-time subscription handshake supplies verification_token in the body.
    verification_token = str(payload.get("verification_token") or "").strip() if isinstance(payload, dict) else ""
    if verification_token:
        # Notion signs the initial handshake with the verification token in its body.
        supplied = headers.get("x-notion-signature", "")
        handshake_signature = "sha256=" + hmac.new(verification_token.encode("utf-8"), raw_body.encode("utf-8"), hashlib.sha256).hexdigest()
        if not supplied or not hmac.compare_digest(handshake_signature, supplied):
            return {"statusCode": 401, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"error": "invalid verification signature"})}
        try:
            _notion_webhook_secret(update_token=verification_token)
            return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"ok": True, "verified": True})}
        except Exception as exc:
            print(json.dumps({"notion_webhook_verification_store_error": str(exc)[:500]}))
            return {"statusCode": 500, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"error": "verification token could not be stored"})}

    # Native Notion events are authenticated with X-Notion-Signature = HMAC-SHA256(raw body).
    supplied = headers.get("x-notion-signature", "")
    try:
        expected_token = _notion_webhook_secret()
    except Exception as exc:
        print(json.dumps({"notion_webhook_secret_read_error": type(exc).__name__}))
        try:
            _record_unverified_delivery(raw_body, "webhook verification secret unavailable", context, event)
        except Exception as ledger_exc:
            _log_event("webhook_persistence_failed", error_type=type(ledger_exc).__name__)
        return {"statusCode": 503, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"error": "webhook verification is not configured"})}
    if not expected_token or not supplied:
        try:
            _record_unverified_delivery(raw_body, "missing signature or verification token", context, event)
        except Exception as exc:
            _log_event("webhook_persistence_failed", error_type=type(exc).__name__)
            return {"statusCode": 503, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"error": "event history is unavailable"})}
        return {"statusCode": 401, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"error": "unauthorized"})}
    calculated = "sha256=" + hmac.new(expected_token.encode("utf-8"), raw_body.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated, supplied):
        try:
            _record_unverified_delivery(raw_body, "invalid signature", context, event)
        except Exception as exc:
            _log_event("webhook_persistence_failed", error_type=type(exc).__name__)
            return {"statusCode": 503, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"error": "event history is unavailable"})}
        _log_event("webhook_rejected", reason="invalid_signature", payload_sha256=hashlib.sha256(raw_body.encode("utf-8")).hexdigest())
        return {"statusCode": 401, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"error": "invalid signature"})}

    if not payload_is_json or not isinstance(payload, dict):
        record_payload = {
            "malformed_json": not payload_is_json,
            "raw_body_sha256": hashlib.sha256(raw_body.encode("utf-8")).hexdigest(),
            "raw_body_size": len(raw_body.encode("utf-8")),
        }
        record_input = _event_record_input(record_payload, raw_body, malformed=not payload_is_json)
        record_input["payload"] = record_payload
        try:
            store = SupabaseIntakeStore()
            recorded = store.record_webhook_event(**record_input)
            row_id = str(recorded.get("id") or "")
            if not row_id.startswith("notion-webhook:"):
                raise IntakeError("Supabase returned no Notion event record ID")
            store.update_webhook_event(row_id, "rejected", error="Webhook body must be a JSON object.", outcome={"validation": "rejected"})
        except Exception as exc:
            _log_event("webhook_persistence_failed", error_type=type(exc).__name__)
            return {"statusCode": 503, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"error": "event history is unavailable"})}
        return {"statusCode": 202, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"ok": True, "recorded": True, "status": "rejected"})}

    entity = payload.get("entity") if isinstance(payload.get("entity"), dict) else {}
    event_type = str(payload.get("type") or payload.get("event_type") or "unknown").strip()[:200] or "unknown"
    event_id = str(payload.get("id") or payload.get("event_id") or "").strip()
    entity_type = str(entity.get("type") or "").strip()
    page_id = str(entity.get("id") or "").strip()
    updated_property_ids = []
    if event_type == "page.properties_updated":
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        changed = data.get("updated_properties") or []
        if isinstance(changed, list):
            updated_property_ids = [value.strip() for value in changed if isinstance(value, str) and value.strip()]
    record_input = _event_record_input(payload, raw_body)
    try:
        store = SupabaseIntakeStore()
        recorded = store.record_webhook_event(**record_input)
        event_row_id = str(recorded.get("id") or "")
        if not event_row_id.startswith("notion-webhook:"):
            raise IntakeError("Supabase returned no Notion event record ID")
    except Exception as exc:
        _log_event("webhook_persistence_failed", error_type=type(exc).__name__)
        return {"statusCode": 503, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"error": "event history is unavailable"})}

    def reject_record(status: str, reason: str):
        store.update_webhook_event(
            event_row_id,
            status,
            aws_request_id=getattr(context, "aws_request_id", ""),
            error=reason if status == "rejected" else "",
            outcome={"validation": status, "reason": reason},
            page_id=record_input.get("page_id") or "",
        )
        _log_event("webhook_recorded_without_processing", event_type=event_type, event_id=event_id, status=status)
        return {"statusCode": 202, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"ok": True, "recorded": True, "status": status, "event_id": event_id or None})}

    if event_id and not _is_uuid(event_id):
        return reject_record("rejected", "Notion event ID is not a UUID.")
    if event_type not in NOTION_PAGE_EVENT_TYPES:
        return reject_record("unsupported", f"Unsupported Notion event type: {event_type}.")
    if entity_type != "page" or not _is_uuid(page_id):
        return reject_record("rejected", "Notion page event has no valid page entity ID.")
    if not recorded.get("should_enqueue"):
        _log_event("webhook_duplicate", page_id=page_id, event_type=event_type, event_id=event_id, status=recorded.get("status", "unknown"))
        return {"statusCode": 202, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"ok": True, "accepted": True, "duplicate": True, "page_id": page_id, "event_id": event_id or None})}

    try:
        _enqueue_worker(
            page_id,
            context.invoked_function_arn,
            event_type=event_type,
            event_id=event_id,
            event_row_id=event_row_id,
            attempt_number=record_input.get("attempt_number"),
            updated_property_ids=updated_property_ids,
        )
    except Exception as exc:
        try:
            store.update_webhook_event(
                event_row_id,
                "failed",
                aws_request_id=getattr(context, "aws_request_id", ""),
                error=f"Worker enqueue failed: {type(exc).__name__}: {str(exc)[:1400]}",
                outcome={"enqueue": "failed"},
                page_id=page_id,
            )
        except Exception as ledger_exc:
            _log_event("event_history_update_failed", event_row_id=event_row_id, error_type=type(ledger_exc).__name__)
        _log_event("notion_intake_enqueue_error", page_id=page_id, event_id=event_id, error_type=type(exc).__name__)
        return {"statusCode": 500, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"error": "intake enqueue failed"})}

    try:
        store.update_webhook_event(event_row_id, "queued", aws_request_id=getattr(context, "aws_request_id", ""), page_id=page_id)
    except Exception as exc:
        _log_event("event_queue_status_update_failed", event_row_id=event_row_id, error_type=type(exc).__name__)
        return {"statusCode": 503, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"error": "event queue status could not be recorded"})}
    _log_event("webhook_accepted", page_id=page_id, event_type=event_type, event_id=event_id, event_row_id=event_row_id,
               aws_request_id=getattr(context, "aws_request_id", ""))
    return {"statusCode": 202, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"ok": True, "accepted": True, "page_id": page_id, "event_id": event_id or None})}
