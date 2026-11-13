"""Idempotent Notion property intake adapter over the canonical Inventory pipeline."""
from __future__ import annotations

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
from shared.google_maps import GoogleMapsClient
from shared.google_sheets import schema
from shared.google_sheets.client import GoogleSheetsClient, GoogleSheetsCredentials

try:
    from . import pipeline
except ImportError:
    import pipeline

NOTION_VERSION = "2022-06-28"
INTAKE_DATABASE_ID = "89dad7a3990849ca9dc23e5bcb3fa99f"
LISTINGS_DATABASE_ID = "bccfd4f55e294b269daa093a928f873a"
MAX_IMAGES = 10
MAX_IMAGE_BYTES = 20 * 1024 * 1024
ALLOWED_FILE_HOSTS = {"secure.notion-static.com", "prod-files-secure.s3.us-west-2.amazonaws.com"}


class IntakeError(RuntimeError):
    pass


def _log_event(event: str, **fields):
    """Emit structured, non-secret operational evidence for every Notion event."""
    print(json.dumps({"service": "efps-notion-intake", "event": event, **fields}, sort_keys=True, default=str))


class NotionClient:
    def __init__(self, token: str, *, session=None):
        if not token:
            raise IntakeError("NOTION_API_TOKEN is not configured")
        self.token = token
        self.session = session or requests.Session()

    def request(self, method: str, path: str, *, payload=None):
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
        if not response.ok:
            raise IntakeError(f"Notion API {method} {path} failed ({response.status_code})")
        return response.json() if response.content else {}

    def get_page(self, page_id: str):
        return self.request("GET", f"pages/{page_id}")

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

    def save_listing(self, row: dict):
        properties = listing_notion_properties(row)
        existing = self.find_listing(str(row["listing_id"]))
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
    row = {name: _notion_value(properties.get(name) or {}) for name in schema.NAMES[:-2]}
    for name in ("Property", "WhatsApp Group", "whatsapp_post", "WhatsApp Destination"):
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
    "BHK", "bachelor_preference", "catalog_title", "city", "cloudinary_image_urls",
    "error_notes", "flat_furnishings", "floor_number", "furnish_type", "intake_status",
    "internal_property_type", "landmark", "listing_id", "listing_state", "locality",
    "maintenance", "meta_catalog_id", "meta_catalog_status", "onboarded_on", "open_parking",
    "posted_at", "preferred_tenant_type", "property_highlights", "property_subtype",
    "raw_message_text", "society_amenities", "society_name", "status", "transaction_type",
    "whatsapp_post",
}
NUMBER_FIELDS = {
    "age_of_property_years", "balconies", "bathrooms", "built_up_area", "carpet_area",
    "covered_parking", "monthly_rent", "pincode", "security_deposit", "total_floors",
}
URL_FIELDS = {"google_maps_url", "posted_url", "whatsapp_contact_link", "whatsapp_group_link"}


def listing_notion_properties(row: dict) -> dict:
    """Project only supported Housing Listings fields; AU/AV remain outside this path."""
    title = str(row.get("catalog_title") or row.get("listing_id") or "").strip()[:2000]
    properties = {"Property": {"title": [{"type": "text", "text": {"content": title}}]}}
    for field in TEXT_FIELDS:
        properties[field] = _rich(row.get(field, ""))
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
    if re.search(r"\b(?:no\s+pets?|pets?\s+not\s+allowed|pets?\s+prohibited|not\s+pet\s+friendly)\b", text, re.I):
        return "Not Allowed"
    if re.search(r"\b(?:pets?\s+allowed|pet\s+friendly|pets?\s+welcome)\b", text, re.I):
        return "Allowed"
    return ""


def _available_from(raw_text: str) -> str:
    text = str(raw_text or "")
    match = re.search(r"\b(?:available\s+from|available\s+on|availability)\s*[:\-]\s*([^\n\r]+)", text, re.I)
    if not match:
        return "Ready to Occupy" if re.search(r"\b(?:ready\s+to\s+occupy|immediately\s+available|available\s+immediately)\b", text, re.I) else ""
    value = match.group(1).strip(" .;")
    return "Ready to Occupy" if re.search(r"\b(?:now|immediate|immediately|ready\s+to\s+occupy)\b", value, re.I) else value


def build_whatsapp_post(row: dict, raw_text: str, *, maps_verified: bool, verified_society_name: str = "") -> str:
    """Build the v7.1 copy/paste caption using only explicit or Maps-verified facts."""
    maps_url = str(row.get("google_maps_url") or "").strip()
    if maps_url and not maps_verified:
        return ""
    locality = str(row.get("locality") or "").strip()
    if not locality:
        return ""
    title_parts = [str(row.get("furnish_type") or "").strip(), str(row.get("BHK") or "").strip()]
    title = " ".join(x for x in title_parts if x)
    raw = str(raw_text or "")
    features = []
    if re.search(r"\bprivate\s+terrace\b", raw, re.I): features.append("Private Terrace")
    if re.search(r"\butility\b", raw, re.I): features.append("Utility")
    attached = re.search(r"\b(\d+)\s+attached\s+bathrooms?\b", raw, re.I)
    if attached: features.append(f"{attached.group(1)} Attached Bathrooms")
    elif row.get("bathrooms"):
        count = str(row["bathrooms"]).strip()
        features.append(f"{count} Bathroom" + ("" if count == "1" else "s"))
    balconies = str(row.get("balconies") or "").strip()
    if balconies and balconies not in {"0", "0.0"}:
        features.append(f"{balconies} " + ("Balcony" if balconies == "1" else "Balconies"))
    if features: title += (" with " if title else "") + " & ".join(features[:3])
    if not title: title = str(row.get("catalog_title") or row.get("listing_id") or "").strip()
    if not title: return ""
    lines = [f"*👉{title}*"]
    rent = _compact_amount(row.get("monthly_rent"))
    if rent: lines.append(f"Rent: {rent}")
    maintenance = str(row.get("maintenance") or "").strip()
    if str(row.get("maintenance_included") or "").strip().lower() == "yes": maintenance = "Included"
    if maintenance: lines.append(f"Maintenance: {maintenance}")
    deposit = _compact_amount(row.get("security_deposit"))
    if deposit: lines.append(f"Deposit: {deposit}")
    sqft = str(row.get("built_up_area") or "").strip()
    if sqft: lines.append(f"Sqft: {sqft}")
    floor = str(row.get("floor_number") or "").strip()
    total_floors = str(row.get("total_floors") or "").strip()
    if floor and total_floors and "/" not in floor and floor.lower() not in {"villa", "independent house", "duplex"}:
        floor = f"{floor}/{total_floors}"
    if floor: lines.append(f"Floor: {floor}")
    availability = _available_from(raw)
    if availability: lines.append(f"Available from: {availability}")
    tenant = str(row.get("preferred_tenant_type") or "").strip()
    if tenant:
        tenant = "Open For All" if tenant.lower() in {"anyone", "open for all"} else tenant
        lines.append(f"Preferred tenant: {tenant}")
    pets = _explicit_pet_policy(raw)
    if pets: lines.append(f"Pets: {pets}")
    if str(row.get("internal_property_type") or "").strip() == "Gated Community": lines.append("Gated Community")
    lines.append(f"Location: *{locality}*")
    if maps_url and _short_mobile_maps_url(maps_url):
        society = str(verified_society_name or ("" if maps_url else row.get("society_name") or "")).strip()
        landmark = str(row.get("landmark") or "").strip()
        label = society if society and society.casefold() != locality.casefold() else ("Landmark" if landmark and landmark.casefold() != locality.casefold() else "")
        if label: lines.extend(["", f"*📍 {label}:", maps_url])
    return "\n".join(lines)


def _row_for_listing(client: GoogleSheetsClient, listing_id: str):
    rows = client.read_range(schema.SHEET_ID, schema.WORKSHEET_NAME, "A2:AT")
    for row_number, values in enumerate(rows, start=2):
        padded = list(values) + [""] * (schema.GRID_WIDTH - len(values))
        row = schema.row_to_mapping(padded)
        if str(row.get("listing_id") or "") == listing_id:
            return row_number, row
    return None


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


def _runtime_sheets_client() -> GoogleSheetsClient:
    raw = _aws_secret_value("GOOGLE_SHEETS_SECRET_ARN")
    try:
        service_account = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise IntakeError("Google Sheets service-account secret is not valid JSON") from exc
    if not isinstance(service_account, dict) or not service_account.get("private_key"):
        raise IntakeError("Google Sheets service-account secret is missing private_key")
    return GoogleSheetsClient(credentials=GoogleSheetsCredentials(service_account))


def _runtime_cloudinary_client() -> CloudinaryClient:
    try:
        values = json.loads(_aws_secret_value("CLOUDINARY_SECRET_ARN"))
    except json.JSONDecodeError as exc:
        raise IntakeError("Cloudinary secret is not valid JSON") from exc
    required = ("cloud_name", "api_key", "api_secret")
    if not isinstance(values, dict) or any(not str(values.get(key) or "").strip() for key in required):
        raise IntakeError("Cloudinary secret is missing required credential fields")
    return CloudinaryClient(credentials=CloudinaryCredentials(**{key: str(values[key]) for key in required}))


def _runtime_maps_client() -> GoogleMapsClient:
    raw = _aws_secret_value("MAPS_SECRET_ARN")
    try:
        parsed = json.loads(raw)
        key = parsed.get("api_key", "") if isinstance(parsed, dict) else raw
    except json.JSONDecodeError:
        key = raw
    if not str(key).strip() or str(key).strip() == "MIGRATION_PLACEHOLDER":
        raise IntakeError("Google Maps API secret is not configured with a live key")
    return GoogleMapsClient(api_key=str(key).strip())


def process_page(
    page_id: str,
    *,
    event_type: str = "",
    updated_property_ids: list[str] | None = None,
    notion: NotionClient | None = None,
    store: SupabaseIntakeStore | None = None,
    sheets: GoogleSheetsClient | None = None,
    cloudinary: CloudinaryClient | None = None,
    maps_client=None,
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
    parent = page.get("parent") or {}
    parent_database_id = str(parent.get("database_id") or parent.get("data_source_id") or "").replace("-", "").lower()
    if parent_database_id == LISTINGS_DATABASE_ID:
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
            _log_event(
                "intake_property_update_ignored",
                page_id=page_id,
                updated_property_count=len(changed_ids),
            )
            return {"status": "ignored", "listing_id": ""}

    sheets = sheets or _runtime_sheets_client()
    cloudinary = cloudinary or _runtime_cloudinary_client()
    raw_text = _plain_text(props.get("Raw Property Data") or {})
    if not raw_text:
        note = "Raw Property Data is required before processing."
        notion.update_page(page_id, {
            "Intake Status": {"status": {"name": "Needs Review"}},
            "Processing Notes": _rich(note),
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
        if not listing_id:
            listing_id = pipeline.next_listing_id(sheets)
            store.set_listing_id(page_id, listing_id)
        notion.update_page(page_id, {"Intake Status": {"status": {"name": "Processing"}}, "Listing ID": _rich(listing_id)})
        found = _row_for_listing(sheets, listing_id)
        if found:
            row_number, row = found
            row["raw_message_text"] = raw_text
        else:
            row_number = 2
            row = pipeline.initial_row(listing_id, raw_text, str(page.get("created_time") or datetime.now(timezone.utc).isoformat()))
            pipeline.write_new_property(sheets, row)

        urls, photo_issues = _upload_photos(page, listing_id, row, cloudinary)
        if urls:
            row["cloudinary_image_urls"] = catalog_urls([Upload(url=u, public_id="", index=i) for i, u in enumerate(urls, start=1)])
        processed, issues = pipeline.process_closed_session(raw_text, row=row, maps_client=maps_client or _runtime_maps_client())
        issues.extend(photo_issues)
        if photo_issues:
            processed["status"] = "Needs Review"
        processed["cloudinary_image_urls"] = row.get("cloudinary_image_urls", processed.get("cloudinary_image_urls", ""))
        maps_url = str(processed.get("google_maps_url") or "").strip()
        maps_failed = bool(maps_url) and any(issue.startswith("Google Maps verification failed") for issue in issues)
        if maps_url and not _short_mobile_maps_url(maps_url):
            issues.append("Original Maps URL is not a supported short mobile link; omitted from the caption and requires review.")
            processed["status"] = "Needs Review"
        verified_society = next((issue.split(":", 1)[1].strip() for issue in issues if issue.startswith("Google Maps verified place name:")), "")
        caption = build_whatsapp_post(processed, raw_text, maps_verified=not maps_failed, verified_society_name=verified_society)
        if not caption:
            issues.append("WhatsApp caption not generated because a verified locality or Maps verification is missing.")
            processed["status"] = "Needs Review"
        processed["whatsapp_post"] = caption
        sheet_projection = {name: processed[name] for name in schema.NAMES}
        pipeline.write_phase1_update(sheets, row_number, sheet_projection)
        listing_page_id = notion.save_listing(processed)
        final_state = "Needs Review" if processed.get("status") == "Needs Review" else "Processed"
        note = "; ".join(issues) if issues else "Processed through the canonical EFPS inventory pipeline."
        notion.update_page(page_id, {
            "Intake Status": {"status": {"name": final_state}},
            "Listing ID": _rich(listing_id),
            "Processing Notes": _rich(note),
            "Processed At": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
            "Processed Property": {"relation": [{"id": listing_page_id}]},
        })
        store.finish(page_id, "needs_review" if final_state == "Needs Review" else "processed", listing_page_id=listing_page_id, note=note)
        return {"status": final_state, "listing_id": listing_id, "listing_page_id": listing_page_id, "issues": issues}
    except Exception as exc:
        note = f"Processing failed: {str(exc)[:1500]}"
        try:
            notion.update_page(page_id, {"Intake Status": {"status": {"name": "Needs Review"}}, "Listing ID": _rich(listing_id), "Processing Notes": _rich(note)})
        finally:
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
            "updated_property_ids": updated_property_ids or [],
        }).encode("utf-8"),
    )
    if int(response.get("StatusCode") or 0) != 202:
        raise IntakeError("Notion intake worker enqueue was not accepted")


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


def lambda_handler(event, context):
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
        updated_property_ids = event.get("updated_property_ids") or []
        if not re.fullmatch(r"[0-9a-fA-F-]{32,36}", page_id):
            raise IntakeError("Invalid asynchronous intake page ID")
        started = time.monotonic()
        _log_event("worker_started", page_id=page_id, event_type=event_type, event_id=event_id, aws_request_id=getattr(context, "aws_request_id", ""))
        try:
            result = process_page(
                page_id,
                event_type=event_type,
                updated_property_ids=updated_property_ids,
            )
        except Exception as exc:
            _log_event("worker_failed", page_id=page_id, event_type=event_type, event_id=event_id,
                       aws_request_id=getattr(context, "aws_request_id", ""), error_type=type(exc).__name__, error=str(exc)[:1000],
                       duration_ms=round((time.monotonic() - started) * 1000))
            raise
        _log_event("worker_completed", page_id=page_id, event_type=event_type, event_id=event_id,
                   aws_request_id=getattr(context, "aws_request_id", ""), status=result.get("status", "unknown"),
                   listing_id=result.get("listing_id", ""), duration_ms=round((time.monotonic() - started) * 1000))
        return result

    headers = {str(k).lower(): str(v) for k, v in (event.get("headers") or {}).items()}
    raw_body = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        import base64
        raw_body = base64.b64decode(raw_body).decode("utf-8")
    try:
        payload = json.loads(raw_body)
    except (json.JSONDecodeError, TypeError, UnicodeDecodeError):
        return {"statusCode": 400, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"error": "invalid JSON"})}

    # Notion's one-time subscription handshake supplies verification_token in the body.
    verification_token = str(payload.get("verification_token") or "").strip()
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
        print(json.dumps({"notion_webhook_secret_read_error": str(exc)[:500]}))
        return {"statusCode": 503, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"error": "webhook verification is not configured"})}
    if not expected_token or not supplied:
        return {"statusCode": 401, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"error": "unauthorized"})}
    calculated = "sha256=" + hmac.new(expected_token.encode("utf-8"), raw_body.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated, supplied):
        return {"statusCode": 401, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"error": "invalid signature"})}

    page_id = str(
        payload.get("page_id")
        or (payload.get("entity") or {}).get("id")
        or (payload.get("data") or {}).get("page", {}).get("id")
        or (payload.get("data") or {}).get("id")
        or payload.get("page", {}).get("id")
        or payload.get("id")
        or ""
    ).strip()
    if not re.fullmatch(r"[0-9a-fA-F-]{32,36}", page_id):
        return {"statusCode": 400, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"error": "page ID is required"})}
    event_type = str(payload.get("type") or payload.get("event_type") or "")
    event_id = str(payload.get("id") or payload.get("event_id") or "")
    updated_property_ids = []
    if event_type == "page.properties_updated":
        data = payload.get("data") or {}
        changed = data.get("updated_properties") or []
        if isinstance(changed, list):
            updated_property_ids = [value.strip() for value in changed if isinstance(value, str) and value.strip()]
    try:
        _log_event("webhook_accepted", page_id=page_id, event_type=event_type, event_id=event_id,
                   aws_request_id=getattr(context, "aws_request_id", ""))
        _enqueue_worker(
            page_id,
            context.invoked_function_arn,
            event_type=event_type,
            event_id=event_id,
            updated_property_ids=updated_property_ids,
        )
        return {"statusCode": 202, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"ok": True, "accepted": True, "page_id": page_id, "event_id": event_id})}
    except Exception as exc:
        print(json.dumps({"notion_intake_enqueue_error": str(exc)[:1500], "page_id": page_id}))
        return {"statusCode": 500, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"error": "intake enqueue failed"})}
