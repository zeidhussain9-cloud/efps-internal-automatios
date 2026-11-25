"""Meta catalogue description generator and WhAPI publisher."""
from __future__ import annotations
import re
from datetime import datetime, date
from typing import Any, Mapping
from shared.whatsapp_whapi.client import WhApiClient

# Google Sheets persistence is retired (Notion is canonical). Callers record
# publish results themselves; pass recorder(product_id) to publish_product.


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


def generate_description(row: Mapping[str, Any]) -> tuple[str, str]:
    title = str(row.get("catalog_title") or "").strip()
    if not title:
        title = f"{row.get('furnish_type', '')} {row.get('BHK', '')} for Rent".strip()

    internal_type = str(row.get("internal_property_type") or "").strip()
    society = str(row.get("society_name") or "").strip()
    locality = str(row.get("locality") or "").strip()
    landmark = str(row.get("landmark") or "").strip()
    raw_text = str(row.get("raw_message_text") or "")

    # Detect if society is real (different from locality/landmark)
    real_society = society if society and society != locality and society != landmark else ""

    # Build description body with bullet format
    lines = []

    # Line 1: • Bathrooms • Balconies
    bathrooms = str(row.get("bathrooms") or "").strip()
    balconies = str(row.get("balconies") or "").strip()
    line1_parts = []
    if bathrooms:
        line1_parts.append(f"{bathrooms} Bathroom{'s' if bathrooms != '1' else ''}")
    if balconies:
        line1_parts.append(f"{balconies} Balcon{'ies' if balconies != '1' else 'y'}")
    if line1_parts:
        lines.append("• " + " • ".join(line1_parts))

    # Line 2: • Area Sq.Ft • Floor
    area = row.get("carpet_area") or row.get("built_up_area")
    floor_num = str(row.get("floor_number") or "").strip()
    total_floors = str(row.get("total_floors") or "").strip()
    if area and floor_num and total_floors:
        lines.append(f"• {_indian_currency(area)} Sq.Ft • {floor_num}{'th' if floor_num else ''} of {total_floors} floors")
    elif area:
        lines.append(f"• {_indian_currency(area)} Sq.Ft")

    # Line 3: • Tenant • Pet Friendly
    tenant = str(row.get("preferred_tenant_type") or "").strip()
    pet = str(row.get("pet_friendly") or "").strip()
    line3_parts = []
    if tenant:
        line3_parts.append(tenant)
    if pet and pet != "-":
        pet_text = "Pet Friendly" if pet.lower() in ["yes", "y"] else "Not Pet Friendly"
        line3_parts.append(pet_text)
    if line3_parts:
        lines.append("• " + " • ".join(line3_parts))

    # Empty line
    lines.append("")

    # Deposit, Maintenance, Available From
    deposit = row.get("security_deposit")
    if deposit:
        lines.append(f"• Deposit ₹{_indian_currency(deposit)}")

    maint = row.get("maintenance")
    maint_included = str(row.get("maintenance_included") or "").strip().lower()
    if maint_included in ("yes", "included"):
        lines.append("• Maintenance: Included")
    elif maint:
        maint_str = str(maint).strip()
        lines.append(f"• Maintenance: {maint_str}")

    avail = _available_from(raw_text)
    if avail:
        lines.append(f"• Available From: {avail}")

    # Empty line before footer
    lines.append("")

    # Footer: show society name or "📍 Landmark:"
    if real_society:
        lines.append(f"*📍{real_society}:*")
    else:
        lines.append("*📍Landmark:*")

    body = "\n".join(lines)

    # Return title WITH emoji for name field, description without title repetition
    title_with_emoji = f"\U0001f3e1 {title}"
    return title_with_emoji, body


def _record_published(recorder, product_id: str) -> None:
    # Sheet write-back is retired. The catalogue rebuild (fix-plan item 15)
    # will record meta_catalog_id/status in Notion via this callback.
    if recorder:
        recorder(product_id)


def publish_product(
    row: Mapping[str, Any],
    *,
    whapi: WhApiClient | None = None,
    recorder=None,
) -> dict:
    """Create or reconcile a WhatsApp Business product for the given property row.

    Returns a dict with keys: status, product_id, listing_id.
    Raises ValueError or RuntimeError on unrecoverable failure.
    """
    listing_id = str(row.get("listing_id") or "")
    if not listing_id:
        raise ValueError("listing_id is missing")

    client = whapi or WhApiClient()

    # Idempotency: if the product already exists in WhatsApp, sync and return
    existing = client.find_product_by_retailer_id(listing_id)
    if existing:
        product_id = str(existing.get("id") or "")
        _record_published(recorder, product_id)
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
                _record_published(recorder, product_id)
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
                    if isinstance(c, dict) else repr(c)
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

    # WhAPI occasionally returns a plain error string instead of a dict
    # (e.g. "Image limit exceeded: max 10 images").  Calling .get() on a
    # string raises AttributeError and crashes the caller.  Surface it as a
    # RuntimeError so the broad except in the thread handler catches it cleanly.
    if isinstance(result, str):
        raise RuntimeError(f"{listing_id}: WhAPI error response: {result}")

    product_id = str(result.get("id") or result.get("product_id") or "")
    if not product_id:
        raise RuntimeError(f"WhAPI returned no product ID: {result}")

    _record_published(recorder, product_id)
    return {
        "status": "created",
        "product_id": product_id,
        "listing_id": listing_id,
    }
