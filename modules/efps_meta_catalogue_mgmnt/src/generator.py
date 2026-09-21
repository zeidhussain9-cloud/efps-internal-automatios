"""Meta catalogue description generator and WhAPI publisher."""
from __future__ import annotations
import re
import time
from datetime import datetime, date
from typing import Any, Mapping
from shared.google_sheets.client import GoogleSheetsClient
from shared.google_sheets import schema
from shared.whatsapp_whapi.client import WhApiClient

# Minimum seconds to wait between product creation and collection assignment.
# WhAPI returns 429 if the assignment call follows the create call too quickly.
_COLLECTION_ASSIGN_COOLDOWN_SECONDS = 30

# BHK-to-collection mapping.  Keys are canonical internal keys;
# values must be substrings of the live WhatsApp collection names.
COLLECTION_NAMES = {
    "1RK_1BHK": "1RK & 1BHK",
    "2BHK": "2BHK",
    "3BHK": "3BHK",
    "4plus_BHK": "4+ BHK",
}


def _indian_currency(value: Any) -> str:
    try:
        num = int(value)
    except (ValueError, TypeError):
        return str(value or "")
    if num < 1000:
        return str(num)
    s = str(num)
    last3 = s[-3:]
    rest = s[:-3]
    groups = []
    while rest:
        groups.insert(0, rest[-2:])
        rest = rest[:-2]
    return ",".join(groups) + "," + last3


def _available_from(raw_text: str) -> str:
    m = re.search(r"(?:available\s+from|move[\s-]*in)\s*[:\-–]\s*(.+)", raw_text, re.I)
    if not m:
        return ""
    val = m.group(1).strip().split("\n")[0].strip()
    if re.match(r"(?:immediate|immediately|now|today|ready|asap)", val, re.I):
        return "Ready to Occupy"
    for fmt in ("%B %d", "%d %B", "%B %d, %Y", "%d %B %Y", "%d %b %Y", "%b %d", "%d/%m/%Y"):
        try:
            parsed = datetime.strptime(val, fmt).date()
            if parsed.year < 2000:
                parsed = parsed.replace(year=date.today().year)
            if parsed <= date.today():
                return "Ready to Occupy"
            return val
        except ValueError:
            continue
    return val


def get_image_urls(row: Mapping[str, Any], limit: int = 10) -> list[str]:
    urls_str = str(row.get("cloudinary_image_urls", "") or "")
    if not urls_str:
        return []
    return [u.strip() for u in urls_str.replace(",", " ").split() if u.strip()][:limit]


def _bhk_to_collection_key(bhk: str) -> str:
    """Map a BHK string to one of the four canonical collection keys."""
    try:
        bhk_num = float(str(bhk or "").strip().split()[0])
        if bhk_num <= 1.5:
            return "1RK_1BHK"
        elif bhk_num <= 2.5:
            return "2BHK"
        elif bhk_num <= 3.5:
            return "3BHK"
        else:
            return "4plus_BHK"
    except (ValueError, IndexError, AttributeError):
        return "4plus_BHK"


def _resolve_collection(client: WhApiClient, key: str) -> tuple[str, str] | None:
    """Fetch live collections and match by name substring.

    Returns (collection_id, collection_name) or None when the collection
    cannot be found.  Uses substring matching so the emoji prefix in live
    collection names ("🏠 1RK & 1BHK") does not prevent matching.
    """
    target = COLLECTION_NAMES[key]
    for coll in client.get_collections():
        if target in coll.get("name", ""):
            return coll["id"], coll["name"]
    return None


def assign_to_collection(
    product_id: str,
    bhk: str,
    *,
    whapi: WhApiClient | None = None,
) -> tuple[bool, str]:
    """Add a product to its BHK collection.

    Returns (success: bool, message: str).

    Root-cause fix: the PATCH /business/collections/{id} response returns
    the updated collection object — it does NOT return {"status": "APPROVED"}.
    We therefore check that the response is a non-error dict rather than
    looking for a specific status key.

    NOTE: WhAPI enforces a rate limit between product creation and collection
    assignment.  Always wait at least _COLLECTION_ASSIGN_COOLDOWN_SECONDS
    after calling publish_product() before calling this function, or use
    publish_and_assign() which handles the wait automatically.
    """
    client = whapi or WhApiClient()
    key = _bhk_to_collection_key(bhk)

    match = _resolve_collection(client, key)
    if not match:
        error = f"Collection for BHK key '{key}' not found in live catalogue"
        print(f"⚠️  Collection: {error}")
        return False, error

    collection_id, collection_name = match
    try:
        result = client.edit_collection(collection_id, add_products=[product_id])

        # edit_collection() does a PATCH which returns the updated collection
        # object on success, or raises RuntimeError on HTTP error.  A non-None
        # dict that lacks an explicit "error" key means success.
        if isinstance(result, dict) and "error" not in result:
            msg = f"Product {product_id} added to '{collection_name}'"
            print(f"✅ Collection: {msg}")
            return True, msg

        # Unexpected shape — treat as failure but surface the raw response
        error = f"Unexpected WhAPI response shape: {str(result)[:150]}"
        print(f"⚠️  Collection: {error}")
        return False, error

    except RuntimeError as e:
        raw = str(e)
        # 429 means we were too fast after product creation — caller should retry
        if "429" in raw or "Too Many Requests" in raw.lower():
            error = f"Rate-limited (429) — wait {_COLLECTION_ASSIGN_COOLDOWN_SECONDS}s and retry"
            print(f"⚠️  Collection: {error}")
            return False, error
        error = f"Collection API error: {raw}"
        print(f"⚠️  Collection: {error}")
        return False, error
    except Exception as e:
        error = f"Collection API error: {str(e)}"
        print(f"⚠️  Collection: {error}")
        return False, error


def publish_and_assign(
    row_number: int,
    row: Mapping[str, Any],
    *,
    whapi: WhApiClient | None = None,
    sheets: GoogleSheetsClient | None = None,
) -> tuple[dict, bool, str]:
    """Create/reconcile a WhatsApp product and assign it to its BHK collection.

    Handles the mandatory cooldown between creation and assignment automatically.

    Returns: (publish_result, assign_ok, assign_message)
    Raises ValueError or RuntimeError on unrecoverable publish failure.
    """
    result = publish_product(row_number, row, whapi=whapi, sheets=sheets)
    product_id = result["product_id"]
    bhk = str(row.get("BHK") or "").strip()

    # Only wait for newly created products, not already-existing ones.
    if result.get("status") == "created":
        print(
            f"ℹ️  publish_and_assign: waiting {_COLLECTION_ASSIGN_COOLDOWN_SECONDS}s "
            f"before collection assignment for {result.get('listing_id')}"
        )
        time.sleep(_COLLECTION_ASSIGN_COOLDOWN_SECONDS)

    assign_ok, assign_msg = assign_to_collection(product_id, bhk, whapi=whapi)
    return result, assign_ok, assign_msg


def generate_description(row: Mapping[str, Any]) -> tuple[str, str]:
    title = str(row.get("catalog_title") or "").strip()
    if not title:
        title = f"{row.get('furnish_type', '')} {row.get('BHK', '')} for Rent".strip()

    internal_type = str(row.get("internal_property_type") or "").strip()
    society = str(row.get("society_name") or "").strip()
    locality = str(row.get("locality") or "").strip()
    maps_url = str(row.get("google_maps_url") or "").strip()
    raw_text = str(row.get("raw_message_text") or "")

    lines = []

    rent = row.get("monthly_rent")
    if rent:
        lines.append(f"Rent: ₹{_indian_currency(rent)}/mo")
    deposit = row.get("security_deposit")
    if deposit:
        lines.append(f"Deposit: ₹{_indian_currency(deposit)}")
    maint = row.get("maintenance")
    maint_included = str(row.get("maintenance_included") or "").strip().lower()
    if maint_included in ("yes", "included"):
        lines.append("Maintenance: Included")
    elif maint:
        lines.append(f"Maintenance: ₹{_indian_currency(maint)}")

    area = row.get("built_up_area")
    if area:
        lines.append(f"Size: {_indian_currency(area)} sqft")
    floor_num = str(row.get("floor_number") or "").strip()
    total_floors = str(row.get("total_floors") or "").strip()
    if floor_num and total_floors:
        lines.append(f"Floor: {floor_num} of {total_floors}")
    elif floor_num:
        lines.append(f"Floor: {floor_num}")

    tenant = str(row.get("preferred_tenant_type") or "").strip()
    if tenant:
        lines.append(f"Preferred Tenant: {tenant}")

    avail = _available_from(raw_text)
    if avail:
        lines.append(f"Available From: {avail}")

    pet = str(row.get("pet_friendly") or "").strip()
    if pet and pet != "-":
        lines.append(f"Pet Friendly: {pet}")

    body = "\n".join(lines)

    footer_parts = []
    if internal_type in ("Gated Community", "Semi Gated") and society:
        loc = f"{society}, {locality}" if locality and locality != society else society
        footer_parts.append(f"✨ {loc}")
    elif locality:
        footer_parts.append(f"✨ {locality}")
    if maps_url:
        footer_parts.append(f"\U0001f4cd Map: {maps_url}")
    footer = "\n".join(footer_parts)

    description = f"\U0001f3e1 {title}\n\n{body}\n\n{footer}"
    return title, description


def _record_published(
    sheet: GoogleSheetsClient, row_number: int, product_id: str
) -> None:
    sheet.write_range(
        schema.SHEET_ID,
        schema.WORKSHEET_NAME,
        schema.range_for("meta_catalog_id", "meta_catalog_status", row_number),
        [[product_id, "Posted"]],
    )
    sheet.write_range(
        schema.SHEET_ID,
        schema.WORKSHEET_NAME,
        schema.range_for("intake_status", "intake_status", row_number),
        [["Published"]],
    )
    sheet.write_range(
        schema.SHEET_ID,
        schema.WORKSHEET_NAME,
        schema.range_for("error_notes", "error_notes", row_number),
        [[""]],
    )


def publish_product(
    row_number: int,
    row: Mapping[str, Any],
    *,
    whapi: WhApiClient | None = None,
    sheets: GoogleSheetsClient | None = None,
) -> dict:
    """Create or reconcile a WhatsApp Business product for the given property row.

    Returns a dict with keys: status, product_id, listing_id.
    Raises ValueError or RuntimeError on unrecoverable failure.
    """
    listing_id = str(row.get("listing_id") or "")
    if not listing_id:
        raise ValueError("listing_id is missing")

    client = whapi or WhApiClient()
    sheet = sheets or GoogleSheetsClient()

    # Idempotency: if the product already exists in WhatsApp, sync and return
    existing = client.find_product_by_retailer_id(listing_id)
    if existing:
        product_id = str(existing.get("id") or "")
        _record_published(sheet, row_number, product_id)
        return {
            "status": "already_exists",
            "product_id": product_id,
            "listing_id": listing_id,
        }

    title, description = generate_description(row)
    images = get_image_urls(row)
    if not images:
        raise ValueError(f"{listing_id}: no images available — upload photos first")

    rent = 0
    try:
        rent = int(row.get("monthly_rent", 0))
    except (ValueError, TypeError):
        pass

    try:
        result = client.create_product(
            name=title,
            description=description,
            price=rent,
            currency="INR",
            images=images,
            url=str(row.get("google_maps_url") or ""),
            product_retailer_id=listing_id,
        )
    except RuntimeError as exc:
        err = str(exc)
        if "Duplicate Item Code" in err:
            found = client.find_product_by_retailer_id(listing_id)
            if found:
                product_id = str(found.get("id") or "")
                _record_published(sheet, row_number, product_id)
                return {
                    "status": "recovered_duplicate",
                    "product_id": product_id,
                    "listing_id": listing_id,
                }
        if "Duplicate Media" in err:
            conflicts = client.find_products_by_image_url(images)
            if conflicts:
                conflict_ids = [
                    f"{c.get('product_retailer_id', '?')}(id={c.get('id', '?')})"
                    for c in conflicts
                ]
                raise RuntimeError(
                    f"{listing_id}: images already used by WhatsApp product(s): "
                    f"{', '.join(conflict_ids)}. "
                    "Delete the conflicting product or re-upload photos with different images."
                ) from exc
            raise RuntimeError(
                f"{listing_id}: images already used by another WhatsApp product. "
                "Re-upload photos to new Cloudinary URLs and update the sheet."
            ) from exc
        raise

    product_id = str(result.get("id") or result.get("product_id") or "")
    if not product_id:
        raise RuntimeError(f"WhAPI returned no product ID: {result}")

    _record_published(sheet, row_number, product_id)
    return {
        "status": "created",
        "product_id": product_id,
        "listing_id": listing_id,
    }
