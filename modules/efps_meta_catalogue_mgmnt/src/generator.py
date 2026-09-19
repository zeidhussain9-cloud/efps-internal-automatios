"""Meta catalogue description generator and WhAPI publisher."""
from __future__ import annotations
import re
from datetime import datetime, date
from typing import Any, Mapping
from shared.google_sheets.client import GoogleSheetsClient
from shared.google_sheets import schema
from shared.whatsapp_whapi.client import WhApiClient

COLLECTION_MAPPING = {
    "1RK_1BHK": "3633492786810534",
    "2BHK": "1870009094415279",
    "3BHK": "1620981473020102",
    "4plus_BHK": "2220392692158816",
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


def _determine_collection_id(bhk: str) -> str:
    try:
        bhk_str = str(bhk or "").strip()
        bhk_num = float(bhk_str.split()[0])
        if bhk_num == 1 or bhk_num == 1.5:
            return COLLECTION_MAPPING["1RK_1BHK"]
        elif bhk_num == 2 or bhk_num == 2.5:
            return COLLECTION_MAPPING["2BHK"]
        elif bhk_num == 3 or bhk_num == 3.5:
            return COLLECTION_MAPPING["3BHK"]
        else:
            return COLLECTION_MAPPING["4plus_BHK"]
    except (ValueError, IndexError, AttributeError):
        return COLLECTION_MAPPING["4plus_BHK"]


def _add_product_to_collection(client: WhApiClient, product_id: str, bhk: str) -> tuple[bool, str]:
    """Add product to collection by BHK. Returns (success, message)."""
    collection_id = _determine_collection_id(bhk)
    collection_name = next((k for k, v in COLLECTION_MAPPING.items() if v == collection_id), "Unknown")

    try:
        result = client.patch(
            "/business/collections",
            {
                "id": collection_id,
                "add_products": [product_id],
            }
        )

        if result and result.get("status") == "APPROVED":
            msg = f"Product {product_id} added to {collection_name}"
            print(f"✅ Collection: {msg}")
            return True, msg
        else:
            error = f"WhAPI rejected collection add: {result}"
            print(f"⚠️ Collection: {error}")
            return False, error

    except Exception as e:
        error = f"Collection API error: {str(e)}"
        print(f"⚠️ Collection: {error}")
        return False, error


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


def _record_published(sheet: GoogleSheetsClient, row_number: int, product_id: str) -> None:
    sheet.write_range(
        schema.SHEET_ID, schema.WORKSHEET_NAME,
        schema.range_for("meta_catalog_id", "meta_catalog_status", row_number),
        [[product_id, "Posted"]],
    )
    sheet.write_range(
        schema.SHEET_ID, schema.WORKSHEET_NAME,
        schema.range_for("intake_status", "intake_status", row_number),
        [["Published"]],
    )
    sheet.write_range(
        schema.SHEET_ID, schema.WORKSHEET_NAME,
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
    listing_id = str(row.get("listing_id") or "")
    if not listing_id:
        raise ValueError("listing_id is missing")

    client = whapi or WhApiClient()
    sheet = sheets or GoogleSheetsClient()

    existing = client.find_product_by_retailer_id(listing_id)
    if existing:
        product_id = str(existing.get("id") or "")
        _record_published(sheet, row_number, product_id)
        return {"status": "already_exists", "product_id": product_id, "listing_id": listing_id}

    title, description = generate_description(row)
    images = get_image_urls(row)
    if not images:
        raise ValueError(f"{listing_id}: no images available")

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
                return {"status": "recovered_duplicate", "product_id": product_id, "listing_id": listing_id}
        if "Duplicate Media" in err:
            raise RuntimeError(
                f"{listing_id}: images are already used by another WhatsApp product. "
                f"Re-upload photos to new Cloudinary URLs and update the sheet."
            ) from exc
        raise

    product_id = str(result.get("id") or result.get("product_id") or "")
    if not product_id:
        raise RuntimeError(f"WhAPI returned no product ID: {result}")

    _record_published(sheet, row_number, product_id)

    bhk = str(row.get("BHK") or "").strip()
    collection_success, collection_msg = _add_product_to_collection(client, product_id, bhk)

    if not collection_success:
        print(f"⚠️ {listing_id}: Collection assignment failed - {collection_msg}")
        return {"status": "created_no_collection", "product_id": product_id, "listing_id": listing_id, "warning": collection_msg}

    return {"status": "created", "product_id": product_id, "listing_id": listing_id}
