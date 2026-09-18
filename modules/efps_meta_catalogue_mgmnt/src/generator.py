"""
Generates the approved meta catalog text format from a property data dictionary.
"""
from __future__ import annotations
from typing import Mapping, Any, List

def get_image_urls(row: Mapping[str, Any], limit: int = 10) -> List[str]:
    """Extracts up to a 'limit' of Cloudinary URLs from the row."""
    urls_str = row.get("cloudinary_image_urls", "") or ""
    if not urls_str:
        return []
    # URLs can be comma or space-separated
    urls = [url.strip() for url in urls_str.replace(",", " ").split() if url.strip()]
    return urls[:limit]

def _format_currency(value: Any) -> str:
    """Formats a number into an Indian currency string."""
    try:
        num = int(value)
        return f"{num:,}"
    except (ValueError, TypeError):
        return str(value or "—")

def generate_catalog_text(row: Mapping[str, Any]) -> str:
    """
    Generates the full catalog text for a single property row.
    Chooses between Variant A (with society) and Variant B (standalone) automatically.
    """
    # Use a generated title if the dedicated one is missing
    title = str(row.get("meta_catalog_title") or "").strip()
    if not title:
        bhk = row.get("BHK", "")
        prop_type = row.get("property_subtype", "Property")
        locality = row.get("locality", "")
        title = f"{row.get('furnish_type', '')} {bhk} {prop_type} for Rent - {locality}".strip()

    # --- Build Key Details Section ---
    details_section = [
        "🔑 *Key Details:*",
        f"• *Rent:* ₹{_format_currency(row.get('monthly_rent'))} / month",
        f"• *Deposit:* ₹{_format_currency(row.get('security_deposit'))}",
        f"• *Maintenance:* ₹{_format_currency(row.get('maintenance'))}",
        f"• *Size:* {row.get('carpet_area', '—')} sq.ft. Carpet Area",
        f"• *Floor:* {row.get('floor_number', '—')} of {row.get('total_floors', '—')} floors",
        f"• *Age:* {row.get('age_of_property_years', '—')} years old",
        f"• *Available From:* {row.get('available_from') or 'Immediately'}",
        f"• *Preferred Tenant:* {row.get('preferred_tenant_type') or 'Any'}"
    ]

    # --- Build Furnishing Section ---
    furnishing_section = [
        "🛋️ *Furnishing & Amenities:*",
        f"• {row.get('furnish_type') or 'Unfurnished'} unit",
        f"• *Pet-friendly:* {row.get('pet_friendly') or 'N/A'}"
    ]

    # --- Build Location Section (Variant A vs B) ---
    society_name = str(row.get("society_name") or "").strip()
    location_lines = ["📍 *Location:*"]
    if society_name:
        location_lines.append(f"• *Society:* {society_name}")
    location_lines.extend([
        f"• *Area:* {row.get('locality', '—')}, Bengaluru",
        f"• *Map:* View on Google Maps ({row.get('google_maps_url') or 'Not available'})"
    ])
    location_section = "\\n".join(location_lines)

    # --- Assemble the final text ---
    full_text = "\\n\\n".join([
        f"✨ *{title}*",
        "\\n".join(details_section),
        "\\n".join(furnishing_section),
        location_section
    ])
    
    return full_text
