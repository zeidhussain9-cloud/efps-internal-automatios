"""
This module generates the catalog format and publishes it to the WhAPI platform.
"""
from __future__ import annotations
from typing import Mapping, Any, List

# Assuming these are available in the execution environment
from shared.google_sheets.client import GoogleSheetsClient
from shared.google_sheets import schema
from mcp_whapi_mcp_createProduct import createProduct, CreateProductRequest

def get_image_urls(row: Mapping[str, Any], limit: int = 10) -> List[str]:
    """Extracts up to a 'limit' of Cloudinary URLs from the row."""
    urls_str = row.get("cloudinary_image_urls", "") or ""
    if not urls_str:
        return []
    urls = [url.strip() for url in urls_str.replace(",", " ").split() if url.strip()]
    return urls[:limit]

def _format_currency(value: Any) -> str:
    """Formats a number into an Indian currency string."""
    try:
        num = int(value)
        return f"{num:,}"
    except (ValueError, TypeError):
        return str(value or "—")

def generate_catalog_text(row: Mapping[str, Any]) -> tuple[str, str]:
    """Generates the title and body text for the catalog."""
    title = str(row.get("meta_catalog_title") or "").strip()
    if not title:
        bhk = row.get("BHK", "")
        prop_type = row.get("property_subtype", "Property")
        locality = row.get("locality", "")
        title = f"{row.get('furnish_type', '')} {bhk} {prop_type} for Rent - {locality}".strip()

    details_section = [
        "🔑 *Key Details:*",
        f"• *Rent:* ₹{_format_currency(row.get('monthly_rent'))} / month",
        f"• *Deposit:* ₹{_format_currency(row.get('security_deposit'))}",
        f"• *Maintenance:* ₹{_format_currency(row.get('maintenance'))}",
    ]
    
    body = "\\n".join(details_section)
    return title, body

def publish_catalog(row_number: int, row_data: Mapping[str, Any]) -> dict:
    """
    Generates and publishes a catalog item to WhAPI and updates the sheet.
    """
    listing_id = row_data.get("listing_id")
    if not listing_id:
        raise ValueError("Listing ID is missing from row data.")

    # 1. Generate Content
    title, description = generate_catalog_text(row_data)
    image_urls = get_image_urls(row_data)
    
    # 2. Call WhAPI to create the product
    # Assumption: The currency is INR.
    create_request = CreateProductRequest(
        name=title,
        description=description,
        price=int(row_data.get("monthly_rent", 0)),
        currency="INR",
        url=row_data.get("google_maps_url", ""),
        images=image_urls,
        product_retailer_id=listing_id,
        is_hidden=False
    )
    
    try:
        publish_result = createProduct(create_request)
        new_product_id = publish_result.get("id")
        if not new_product_id:
            raise RuntimeError(f"WhAPI createProduct failed: {publish_result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"Failed to publish to WhAPI: {e}")
        # Write error back to sheet
        error_update = [["", f"WhAPI Publish Error: {e}"]]
        GoogleSheetsClient().write_range(schema.SHEET_ID, schema.WORKSHEET_NAME, schema.range_for("meta_catalog_status", "error_notes", row_number), error_update)
        return {"status": "error", "message": str(e)}

    # 3. Write new ID and status back to Google Sheet
    update_values = [[new_product_id, "Posted"]]
    update_range = schema.range_for("meta_catalog_id", "meta_catalog_status", row_number)
    
    try:
        GoogleSheetsClient().write_range(schema.SHEET_ID, schema.WORKSHEET_NAME, update_range, update_values)
    except Exception as e:
        # If sheet write fails, we have an orphan product in WhAPI. Log this critical error.
        error_message = f"CRITICAL: WhAPI product {new_product_id} was created but failed to write back to sheet row {row_number}. Error: {e}"
        print(error_message)
        # Attempt to write error to sheet
        GoogleSheetsClient().write_range(schema.SHEET_ID, schema.WORKSHEET_NAME, schema.range_for("error_notes", "error_notes", row_number), [[error_message]])
        return {"status": "error", "message": "Failed to write back to sheet after successful publish."}

    return {"status": "success", "product_id": new_product_id, "listing_id": listing_id}

