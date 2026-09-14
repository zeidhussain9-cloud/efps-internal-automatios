"""Canonical 48-column Housing_Listings contract and population-stage metadata."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping

SHEET_ID = "1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc"
WORKSHEET_NAME = "Housing_Listings"
CONTRACT_VERSION = 1
PANEL, HOUSING_AGENT, META_CATALOG = "panel", "housing_agent", "meta_catalog"
OWNERS = (PANEL, HOUSING_AGENT, META_CATALOG)

@dataclass(frozen=True)
class Column:
    name: str
    group: str
    owner: str
    stage: str
    allowed_values: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()
    note: str = ""
    @property
    def letter(self) -> str: return col_letter(NAMES.index(self.name))

def col_letter(index0: int) -> str:
    if index0 < 0: raise ValueError("column index cannot be negative")
    out, n = "", index0 + 1
    while n:
        n, rem = divmod(n - 1, 26); out = chr(65 + rem) + out
    return out

# stage values: intake, deterministic_extraction, normalization, maps_resolution,
# validation, ai_verification, ai_beautification, phase_2_media, phase_2_lifecycle, downstream.
# Physical order A:AV is immutable. The stage says when the field is first populated.
_ROWS = [
("listing_id","contract",PANEL,"intake",(),(),"EF-YYMM-XXXX; immutable row identity"),
("status","contract",PANEL,"intake",("Raw","Pending","Needs Review"),(),"Raw at creation; Pending/Needs Review after validation"),
("transaction_type","contract",PANEL,"intake",("Rent",),(),"fixed"),
("society_name","contract",PANEL,"normalization",(),("locality","landmark"),"source/fallback, never guessed"),
("property_subtype","contract",PANEL,"deterministic_extraction",("Apartment","Independent House","Duplex","Independent Floor","Villa","Penthouse","Studio","Farm House"),(),"legacy portal vocabulary normalized here"),
("city","contract",PANEL,"intake",("Bengaluru",),(),"fixed"),
("locality","contract",PANEL,"maps_resolution",(),("google_maps_url",),"Maps-owned"),
("pincode","contract",PANEL,"maps_resolution",(),("google_maps_url",),"Maps-owned; optional"),
("landmark","contract",PANEL,"deterministic_extraction",(),(),"only if stated"),
("BHK","contract",PANEL,"deterministic_extraction",(),(),"explicit source only"),
("built_up_area","contract",PANEL,"deterministic_extraction",(),(),"explicit source only"),
("carpet_area","contract",PANEL,"normalization",(),("built_up_area",),"explicit source wins; legacy safe derivation otherwise"),
("age_of_property_years","contract",PANEL,"deterministic_extraction",(),(),"explicit source only"),
("floor_number","contract",PANEL,"deterministic_extraction",(),("property_subtype",),"blank for standalone types"),
("total_floors","contract",PANEL,"deterministic_extraction",(),(),"explicit source only"),
("bathrooms","contract",PANEL,"deterministic_extraction",(),(),"explicit source only"),
("balconies","contract",PANEL,"deterministic_extraction",(),(),"explicit source only"),
("furnish_type","contract",PANEL,"deterministic_extraction",("Fully Furnished","Semi Furnished","Unfurnished"),(),"explicit source only"),
("flat_furnishings","contract",PANEL,"normalization",(),("furnish_type",),"safe defaults based on furnish type"),
("society_amenities","contract",PANEL,"normalization",(),("property_subtype",),"safe tier defaults only when applicable"),
("covered_parking","contract",PANEL,"deterministic_extraction",("0","1","2","3","3+"),(),"explicit source only"),
("open_parking","contract",PANEL,"deterministic_extraction",(),(),"explicit source only"),
("preferred_tenant_type","contract",PANEL,"deterministic_extraction",(),(),"explicit source only"),
("bachelor_preference","contract",PANEL,"deterministic_extraction",(),("preferred_tenant_type",),"explicit source only"),
("pet_friendly","contract",PANEL,"deterministic_extraction",(),(),"explicit source only"),
("monthly_rent","contract",PANEL,"deterministic_extraction",(),(),"required before canonical validation"),
("maintenance","contract",PANEL,"deterministic_extraction",(),("maintenance_included",),"numeric; zero when included"),
("maintenance_included","contract",PANEL,"deterministic_extraction",("Yes","No"),(),"interdependent with maintenance"),
("security_deposit","contract",PANEL,"normalization",(),("monthly_rent",),"months converted to amount"),
("servant_room","contract",PANEL,"normalization",("Yes","No"),(),"blank defaults to No"),
("google_maps_url","contract",PANEL,"maps_resolution",(),(),"canonical Maps URL/result"),
("catalog_title","contract",PANEL,"ai_beautification",(),(),"wording-only AI output"),
("whatsapp_contact_link","contract",PANEL,"intake",(),(),"fixed company link"),
("whatsapp_group_link","contract",PANEL,"intake",(),(),"fixed company group link"),
("property_highlights","contract",PANEL,"ai_beautification",(),(),"wording-only; no invented facts"),
("cloudinary_image_urls","contract",PANEL,"phase_2_media",(),(),"not populated in Phase 1"),
("posted_url","contract",HOUSING_AGENT,"downstream",(),(),"Housing agent-owned"),
("posted_at","contract",HOUSING_AGENT,"downstream",(),(),"Housing agent-owned"),
("error_notes","contract",HOUSING_AGENT,"downstream",(),(),"Housing agent-owned"),
("meta_catalog_id","contract",META_CATALOG,"downstream",(),(),"Meta catalogue-owned"),
("meta_catalog_status","contract",META_CATALOG,"downstream",(),(),"Meta catalogue-owned"),
("raw_message_text","extra",PANEL,"intake",(),(),"all text between NEW markers, stamped; no media binary"),
("intake_status","extra",PANEL,"intake",("Raw","Processed"),(),"intake bookkeeping"),
("onboarded_on","tail",PANEL,"phase_2_lifecycle",(),(),"broker onboarding date"),
("internal_property_type","tail",PANEL,"normalization",("Gated Community","Semi Gated","Standalone"),(),"internal only"),
("listing_state","tail",PANEL,"phase_2_lifecycle",("Available","Rented Out","On Hold"),(),"lifecycle"),
("source_group","tail",PANEL,"intake",(),(),"source group"),
("inventory_locked","tail",PANEL,"phase_2_lifecycle",("Yes","No"),(),"lock after lifecycle close; not Phase 1"),
]
COLUMNS = tuple(Column(*r) for r in _ROWS)
NAMES = tuple(c.name for c in COLUMNS)
BY_NAME = {c.name:c for c in COLUMNS}
GRID_WIDTH = len(COLUMNS); EXPECTED_GRID_WIDTH = 48
FIRST_COLUMN = "A"; LAST_COLUMN = col_letter(GRID_WIDTH-1); EXPECTED_LAST_COLUMN = "AV"
CONTRACT_NAMES = tuple(c.name for c in COLUMNS if c.group == "contract")
EXTRA_NAMES = tuple(c.name for c in COLUMNS if c.group == "extra")
TAIL_NAMES = tuple(c.name for c in COLUMNS if c.group == "tail")
ROW_IDENTITY = "listing_id"

def letter(name: str) -> str: return BY_NAME[name].letter
def owner_of(name: str) -> str: return BY_NAME[name].owner
def stage_of(name: str) -> str: return BY_NAME[name].stage
def writable_by(owner: str) -> tuple[str,...]:
    if owner not in OWNERS: raise KeyError(owner)
    return tuple(c.name for c in COLUMNS if c.owner == owner)
def assert_writable(owner: str, names: list[str] | tuple[str,...]) -> None:
    allowed=set(writable_by(owner)); unknown=[n for n in names if n not in BY_NAME]
    if unknown: raise KeyError(f"Unknown Housing_Listings field: {', '.join(unknown)}")
    foreign=[n for n in names if n not in allowed]
    if foreign: raise PermissionError(f"{owner} may not write: {', '.join(foreign)}")
def validate_row(values: list[Any] | tuple[Any,...]) -> tuple[Any,...]:
    if len(values)!=GRID_WIDTH: raise ValueError(f"Housing_Listings row must contain {GRID_WIDTH} values; found {len(values)}")
    return tuple(values)
def row_to_mapping(values: list[Any] | tuple[Any,...]) -> dict[str,Any]: return dict(zip(NAMES, validate_row(values)))
def mapping_to_row(values: Mapping[str,Any]) -> list[Any]:
    unknown=[n for n in values if n not in BY_NAME]
    if unknown: raise KeyError(f"Unknown Housing_Listings field: {', '.join(unknown)}")
    return [values.get(n,"") for n in NAMES]
def full_range(first_row:int=1)->str: return f"{FIRST_COLUMN}{first_row}:{LAST_COLUMN}"
def range_for(first:str,last:str,row:int)->str: return f"{letter(first)}{row}:{letter(last)}{row}"

def _check() -> None:
    assert GRID_WIDTH == EXPECTED_GRID_WIDTH and LAST_COLUMN == EXPECTED_LAST_COLUMN
    assert len(CONTRACT_NAMES)==41 and len(EXTRA_NAMES)==2 and len(TAIL_NAMES)==5
    assert letter("posted_url")=="AK" and letter("meta_catalog_status")=="AO"
    assert letter("raw_message_text")=="AP" and letter("inventory_locked")=="AV"
    assert len(set(NAMES))==48
_check()
