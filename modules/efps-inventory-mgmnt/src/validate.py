"""Deterministic validation for the Stage-2 inventory record."""
from __future__ import annotations
import re
from shared.google_sheets import schema

FIXED = {
    "transaction_type": "Rent",
    "city": "Bengaluru",
    "whatsapp_contact_link": "https://wa.me/919148338801",
    "whatsapp_group_link": "https://chat.whatsapp.com/FxOPO0xAOsD6lNwPcIDdFM",
}
PROPERTY_SUBTYPES = {"Apartment", "Independent House", "Duplex", "Independent Floor", "Villa", "Penthouse", "Studio", "Farm House"}
FURNISH_TYPES = {"Fully Furnished", "Semi Furnished", "Unfurnished"}
COVERED_PARKING = {"0", "1", "2", "3", "3+"}
FURNISHINGS = {"AC", "Wardrobe", "Geyser", "Fan", "Light", "Fridge", "TV", "Bed", "Sofa", "Dining Table", "Washing Machine", "Cupboard", "Microwave", "Stove", "Water Purifier", "Gas Pipeline", "Chimney", "Modular Kitchen"}
AMENITIES = {"Semi Gated", "Standalone", "Lift", "Gym", "CCTV", "Power Backup", "Swimming Pool", "Gated Community", "Club House", "Garden", "Intercom", "Sports", "Kids Area", "Community Hall", "Regular Water Supply", "Attached Balcony"}
NUMERIC = {"pincode", "built_up_area", "carpet_area", "age_of_property_years", "total_floors", "bathrooms", "balconies", "open_parking", "monthly_rent", "security_deposit"}


def _numeric(value: object) -> bool:
    return bool(re.fullmatch(r"\d+(?:\.\d+)?", str(value)))


def validate(row: dict) -> list[str]:
    errors: list[str] = []
    if set(row) != set(schema.NAMES):
        return ["row shape does not match canonical 48 fields"]
    for key, value in FIXED.items():
        if row[key] != value:
            errors.append(f"{key} must be {value}")
    if row["status"] not in ("Pending", "Needs Review"):
        errors.append("status must be Pending or Needs Review after extraction")
    if row["intake_status"] not in ("Raw", "Processed"):
        errors.append("intake_status must be Raw or Processed")
    if not row["listing_id"]:
        errors.append("listing_id required")
    if not row["monthly_rent"]:
        errors.append("monthly_rent required")
    if row["BHK"] and not re.fullmatch(r"\d+(?:\.\d+)? BHK", str(row["BHK"])) and row["BHK"] != "1 RK":
        errors.append("invalid BHK")
    if row["property_subtype"] and row["property_subtype"] not in PROPERTY_SUBTYPES:
        errors.append("invalid property_subtype")
    if row["furnish_type"] and row["furnish_type"] not in FURNISH_TYPES:
        errors.append("invalid furnish_type")
    if row["covered_parking"] not in COVERED_PARKING | {""}:
        errors.append("invalid covered_parking")
    for key in NUMERIC:
        if row[key] and not _numeric(row[key]):
            errors.append(f"{key} must be numeric")
    if row["maintenance"] and not _numeric(row["maintenance"]):
        if str(row["maintenance"]).strip().lower() == "included":
            errors.append("maintenance must be 0 when included")
    for key, allowed in (("flat_furnishings", FURNISHINGS), ("society_amenities", AMENITIES)):
        bad = [x.strip() for x in str(row[key]).split(",") if x.strip() and x.strip() not in allowed]
        if bad:
            errors.append(f"{key} invalid values: {bad}")
    if row["maintenance_included"] not in ("Yes", "No", ""):
        errors.append("maintenance_included must be Yes/No/blank")
    if row["maintenance_included"] == "Yes" and row["maintenance"] != "0":
        errors.append("maintenance must be 0 when included")
    if row["internal_property_type"] and row["internal_property_type"] not in {"Gated Community", "Semi Gated", "Standalone"}:
        errors.append("invalid internal_property_type")
    if row["servant_room"] and row["servant_room"] not in {"Yes", "No"}:
        errors.append("servant_room must be Yes/No")
    for key in ("posted_url", "posted_at", "error_notes", "meta_catalog_id", "meta_catalog_status"):
        if row[key]:
            errors.append(f"{key} must remain empty before downstream stages")
    return errors


def validate_raw(row: dict) -> list[str]:
    errors: list[str] = []
    if set(row) != set(schema.NAMES):
        return ["raw row shape does not match canonical 48 fields"]
    if row["status"] != "Raw":
        errors.append("initial row status must be Raw")
    if row["intake_status"] != "Raw":
        errors.append("initial row intake_status must be Raw")
    if not row["listing_id"]:
        errors.append("listing_id required")
    if not row["onboarded_on"]:
        errors.append("onboarded_on required")
    for key, value in FIXED.items():
        if row[key] != value:
            errors.append(f"{key} must be {value}")
    for key in ("listing_state", "posted_url", "posted_at", "error_notes", "meta_catalog_id", "meta_catalog_status", "inventory_locked"):
        if row[key]:
            errors.append(f"{key} must be empty at initial intake")
    return errors
