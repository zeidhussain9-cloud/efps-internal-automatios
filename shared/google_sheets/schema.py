"""Canonical 48-column Housing_Listings contract for EFPS.

The machine-readable legacy contract (`docs/SHEET_CONTRACT.json` in
`efps-platform`) is the verified 48-column A:AV contract. This local module is
the new repository's single maintained representation. Modules must consume it,
not redefine the sheet elsewhere.
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

    @property
    def letter(self) -> str:
        return col_letter(NAMES.index(self.name))


def col_letter(index0: int) -> str:
    if index0 < 0:
        raise ValueError("column index cannot be negative")
    letters = ""
    n = index0 + 1
    while n:
        n, rem = divmod(n - 1, 26)
        letters = chr(ord("A") + rem) + letters
    return letters


# Physical order is authoritative. Do not insert into the middle of this table.
# The final five tail fields are AR:AV; this is why the verified grid is 48
# columns even though the older source schema.py stopped at AU.
_TABLE: tuple[tuple[str, str, str, str], ...] = (
    ("listing_id", "contract", PANEL, "EF-YYMM-XXXX; immutable row identity"),
    ("status", "contract", PANEL, "Raw / Pending / Needs Review"),
    ("transaction_type", "contract", PANEL, "forced to Rent"),
    ("society_name", "contract", PANEL, "D-79 fallback: society -> locality -> landmark; never blank"),
    ("property_subtype", "contract", PANEL, "one of the 8 Housing.com words"),
    ("city", "contract", PANEL, "forced to Bengaluru"),
    ("locality", "contract", PANEL, "Maps-owned; not model-owned"),
    ("pincode", "contract", PANEL, "Maps-owned; not mandatory"),
    ("landmark", "contract", PANEL, ""),
    ("BHK", "contract", PANEL, ""),
    ("built_up_area", "contract", PANEL, ""),
    ("carpet_area", "contract", PANEL, "Pipeline-derived unless broker stated it; D-86"),
    ("age_of_property_years", "contract", PANEL, ""),
    ("floor_number", "contract", PANEL, "blank for villas and independent houses"),
    ("total_floors", "contract", PANEL, ""),
    ("bathrooms", "contract", PANEL, ""),
    ("balconies", "contract", PANEL, ""),
    ("furnish_type", "contract", PANEL, ""),
    ("flat_furnishings", "contract", PANEL, "defaults by furnish_type; AC deliberately excluded"),
    ("society_amenities", "contract", PANEL, ""),
    ("covered_parking", "contract", PANEL, ""),
    ("open_parking", "contract", PANEL, ""),
    ("preferred_tenant_type", "contract", PANEL, ""),
    ("bachelor_preference", "contract", PANEL, ""),
    ("pet_friendly", "contract", PANEL, ""),
    ("monthly_rent", "contract", PANEL, "NOT named 'rent'"),
    ("maintenance", "contract", PANEL, "must be 0 when maintenance_included is Yes"),
    ("maintenance_included", "contract", PANEL, ""),
    ("security_deposit", "contract", PANEL, ""),
    ("servant_room", "contract", PANEL, "defaults to No when unmentioned"),
    ("google_maps_url", "contract", PANEL, ""),
    ("catalog_title", "contract", PANEL, ""),
    ("whatsapp_contact_link", "contract", PANEL, "fixed"),
    ("whatsapp_group_link", "contract", PANEL, "fixed"),
    ("property_highlights", "contract", PANEL, ""),
    ("cloudinary_image_urls", "contract", PANEL, "last panel-written contract column (AJ)"),
    ("posted_url", "contract", HOUSING_AGENT, "housing agent; AK"),
    ("posted_at", "contract", HOUSING_AGENT, "housing agent; AL"),
    ("error_notes", "contract", HOUSING_AGENT, "housing agent; AM"),
    ("meta_catalog_id", "contract", META_CATALOG, "meta-catalog agent; AN"),
    ("meta_catalog_status", "contract", META_CATALOG, "meta-catalog agent; AO"),
    ("raw_message_text", "extra", PANEL, "every WhatsApp message for this property; AP"),
    ("intake_status", "extra", PANEL, "Raw / Processed; AQ"),
    ("onboarded_on", "tail", PANEL, "when the BROKER posted it, not a technical timestamp; AR"),
    ("internal_property_type", "tail", PANEL, "gated / semi-gated / standalone; internal only; AS"),
    ("listing_state", "tail", PANEL, "Available / Rented Out / On Hold; rows are marked, never deleted; AT"),
    ("source_group", "tail", PANEL, "which WhatsApp group the property came from; AU"),
    ("inventory_locked", "tail", PANEL, "Yes once sender closes property with second 'new'; AV; blocks live-inventory edits only"),
)

COLUMNS = tuple(Column(*row) for row in _TABLE)
NAMES = tuple(column.name for column in COLUMNS)
BY_NAME = {column.name: column for column in COLUMNS}
GRID_WIDTH = len(COLUMNS)
FIRST_COLUMN = "A"
LAST_COLUMN = col_letter(GRID_WIDTH - 1)
EXPECTED_GRID_WIDTH = 48
EXPECTED_LAST_COLUMN = "AV"
CONTRACT_NAMES = tuple(c.name for c in COLUMNS if c.group == "contract")
EXTRA_NAMES = tuple(c.name for c in COLUMNS if c.group == "extra")
TAIL_NAMES = tuple(c.name for c in COLUMNS if c.group == "tail")
ALLOWED_VALUES = {"status": ("Raw", "Pending", "Needs Review")}
ROW_IDENTITY = "listing_id"


def letter(name: str) -> str:
    if name not in BY_NAME:
        raise KeyError(f"Unknown Housing_Listings field: {name}")
    return BY_NAME[name].letter


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
        raise PermissionError(f"{owner} may not write: {', '.join(foreign)}")


def full_range(first_row: int = 1) -> str:
    return f"{FIRST_COLUMN}{first_row}:{LAST_COLUMN}"


def range_for(first: str, last: str, row: int) -> str:
    return f"{letter(first)}{row}:{letter(last)}{row}"


def _check() -> None:
    if GRID_WIDTH != EXPECTED_GRID_WIDTH or LAST_COLUMN != EXPECTED_LAST_COLUMN:
        raise AssertionError(
            f"Housing_Listings schema drift: expected {EXPECTED_GRID_WIDTH} columns "
            f"ending {EXPECTED_LAST_COLUMN}, found {GRID_WIDTH} ending {LAST_COLUMN}"
        )
    if len(set(NAMES)) != len(NAMES):
        raise AssertionError("Duplicate Housing_Listings field names")
    if len(CONTRACT_NAMES) != 41 or len(EXTRA_NAMES) != 2 or len(TAIL_NAMES) != 5:
        raise AssertionError("Expected 41 contract + 2 extra + 5 tail fields")
    if letter("posted_url") != "AK" or letter("meta_catalog_status") != "AO":
        raise AssertionError("Foreign ownership block drifted from AK:AO")
    if letter("raw_message_text") != "AP" or letter("inventory_locked") != "AV":
        raise AssertionError("Panel tail block drifted from AP:AV")
    if set(NAMES) != set(writable_by(PANEL)) | set(writable_by(HOUSING_AGENT)) | set(writable_by(META_CATALOG)):
        raise AssertionError("Every column must have exactly one owner")


_check()
