"""Canonical Housing_Listings sheet contract for EFPS.

Derived from the verified legacy efps-platform `modules/efps-whapi-panel/src/schema.py`
and its generated cross-project contract. This file is the local source of truth
for the physical Google Sheet shape and ownership rules used by shared and
calling modules.

Do not create a second competing sheet schema elsewhere. Modules consume this
contract; they do not redefine columns or ownership.
"""

from __future__ import annotations

from dataclasses import dataclass

SHEET_ID = "1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc"
WORKSHEET_NAME = "Housing_Listings"
CONTRACT_VERSION = 1

PANEL = "panel"
HOUSING_AGENT = "housing_agent"
META_CATALOG = "meta_catalog"
OWNERS = (PANEL, HOUSING_AGENT, META_CATALOG)


@dataclass(frozen=True)
class Column:
    name: str
    group: str
    owner: str
    note: str = ""


def col_letter(index0: int) -> str:
    if index0 < 0:
        raise ValueError("column index cannot be negative")
    letters = ""
    n = index0 + 1
    while n:
        n, rem = divmod(n - 1, 26)
        letters = chr(ord("A") + rem) + letters
    return letters


_TABLE: tuple[tuple[str, str, str, str], ...] = (
    ("listing_id", "contract", PANEL, "Immutable row identity"),
    ("status", "contract", PANEL, "Raw / Pending / Needs Review"),
    ("transaction_type", "contract", PANEL, "forced to Rent"),
    ("society_name", "contract", PANEL, "Society/locality/landmark fallback rule"),
    ("property_subtype", "contract", PANEL, "Housing.com property subtype"),
    ("city", "contract", PANEL, "forced to Bengaluru"),
    ("locality", "contract", PANEL, "Maps-owned"),
    ("pincode", "contract", PANEL, "Maps-owned; optional"),
    ("landmark", "contract", PANEL, ""),
    ("BHK", "contract", PANEL, ""),
    ("built_up_area", "contract", PANEL, ""),
    ("carpet_area", "contract", PANEL, "Pipeline-derived unless explicitly stated"),
    ("age_of_property_years", "contract", PANEL, ""),
    ("floor_number", "contract", PANEL, "Blank for villas and independent houses"),
    ("total_floors", "contract", PANEL, ""),
    ("bathrooms", "contract", PANEL, ""),
    ("balconies", "contract", PANEL, ""),
    ("furnish_type", "contract", PANEL, ""),
    ("flat_furnishings", "contract", PANEL, "Defaults by furnish_type"),
    ("society_amenities", "contract", PANEL, ""),
    ("covered_parking", "contract", PANEL, ""),
    ("open_parking", "contract", PANEL, ""),
    ("preferred_tenant_type", "contract", PANEL, ""),
    ("bachelor_preference", "contract", PANEL, ""),
    ("pet_friendly", "contract", PANEL, ""),
    ("monthly_rent", "contract", PANEL, ""),
    ("maintenance", "contract", PANEL, ""),
    ("maintenance_included", "contract", PANEL, ""),
    ("security_deposit", "contract", PANEL, ""),
    ("servant_room", "contract", PANEL, "Defaults to No when unmentioned"),
    ("google_maps_url", "contract", PANEL, ""),
    ("catalog_title", "contract", PANEL, ""),
    ("whatsapp_contact_link", "contract", PANEL, "Fixed"),
    ("whatsapp_group_link", "contract", PANEL, "Fixed"),
    ("property_highlights", "contract", PANEL, ""),
    ("cloudinary_image_urls", "contract", PANEL, "Last panel-written contract field"),
    ("posted_url", "contract", HOUSING_AGENT, "Housing agent"),
    ("posted_at", "contract", HOUSING_AGENT, "Housing agent"),
    ("error_notes", "contract", HOUSING_AGENT, "Housing agent"),
    ("meta_catalog_id", "contract", META_CATALOG, "Meta catalogue agent"),
    ("meta_catalog_status", "contract", META_CATALOG, "Meta catalogue agent"),
    ("raw_message_text", "extra", PANEL, "Stamped inbound WhatsApp messages"),
    ("intake_status", "extra", PANEL, "Raw / Processed"),
    ("onboarded_on", "tail", PANEL, "Broker posting timestamp"),
    ("internal_property_type", "tail", PANEL, "Internal only"),
    ("listing_state", "tail", PANEL, "Available / Rented Out / On Hold"),
    ("source_group", "tail", PANEL, "Source WhatsApp group"),
    ("inventory_locked", "tail", PANEL, "Locks further live inventory edits"),
)

COLUMNS = tuple(Column(*row) for row in _TABLE)
NAMES = tuple(column.name for column in COLUMNS)
BY_NAME = {column.name: column for column in COLUMNS}
GRID_WIDTH = len(COLUMNS)
FIRST_COLUMN = col_letter(0)
LAST_COLUMN = col_letter(GRID_WIDTH - 1)

# Current legacy contract has 48 physical columns A:AV. The canonical table
# above is intentionally expected to remain synchronized with that contract.
EXPECTED_GRID_WIDTH = 48
EXPECTED_LAST_COLUMN = "AV"

ALLOWED_VALUES = {
    "status": ("Raw", "Pending", "Needs Review"),
}


def letter(name: str) -> str:
    try:
        return col_letter(NAMES.index(name))
    except ValueError:
        raise KeyError(f"Unknown Housing_Listings field: {name}") from None


def owner_of(name: str) -> str:
    return BY_NAME[name].owner


def writable_by(owner: str) -> tuple[str, ...]:
    if owner not in OWNERS:
        raise KeyError(owner)
    return tuple(column.name for column in COLUMNS if column.owner == owner)


def assert_writable(owner: str, names: list[str] | tuple[str, ...]) -> None:
    allowed = set(writable_by(owner))
    foreign = [name for name in names if name not in allowed]
    if foreign:
        raise PermissionError(
            f"{owner} may not write: {', '.join(foreign)}"
        )


def full_range(first_row: int = 1) -> str:
    return f"{FIRST_COLUMN}{first_row}:{LAST_COLUMN}"


# Legacy cross-project rule: panel owns the inventory fields plus raw/tail;
# housing agent owns AK:AM; meta catalog owns AN:AO. This must remain machine-
# checked when the table is changed.
def _check() -> None:
    if GRID_WIDTH != EXPECTED_GRID_WIDTH or LAST_COLUMN != EXPECTED_LAST_COLUMN:
        raise AssertionError(
            f"Housing_Listings schema drift: expected {EXPECTED_GRID_WIDTH} columns "
            f"ending {EXPECTED_LAST_COLUMN}, found {GRID_WIDTH} ending {LAST_COLUMN}"
        )
    if len(set(NAMES)) != len(NAMES):
        raise AssertionError("Duplicate Housing_Listings field names")
    if set(owner for owner in OWNERS) != {PANEL, HOUSING_AGENT, META_CATALOG}:
        raise AssertionError("Invalid owner definitions")
    if set(NAMES) != set(writable_by(PANEL)) | set(writable_by(HOUSING_AGENT)) | set(writable_by(META_CATALOG)):
        raise AssertionError("Not every Housing_Listings field has exactly one owner")


_check()
