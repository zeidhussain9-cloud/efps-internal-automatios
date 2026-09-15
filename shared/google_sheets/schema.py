"""Canonical Housing_Listings contract and three-stage population metadata."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping

SHEET_ID = "1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc"
WORKSHEET_NAME = "Housing_Listings"
CONTRACT_VERSION = 4
PANEL, HOUSING_AGENT, META_CATALOG = "panel", "housing_agent", "meta_catalog"
OWNERS = (PANEL, HOUSING_AGENT, META_CATALOG)
STAGE_1 = "initial_webhook"
STAGE_2 = "deterministic_extraction_property_processing"
STAGE_3 = "downstream_operations"

@dataclass(frozen=True)
class Column:
    name: str
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

_ROWS = [
("listing_id",PANEL,STAGE_1,(),(),"Immutable row identity; EF-YYMM-XXXX."),
("status",PANEL,STAGE_1,("Raw","Pending","Needs Review"),(),"Raw at creation; Pending after a valid deterministic Phase-1 boundary; Needs Review on deterministic/runtime validation failure."),
("intake_status",PANEL,STAGE_1,("Raw","Processed"),(),"Raw at creation; Processed after successful intake + deterministic extraction attempt."),
("internal_property_type",PANEL,STAGE_2,("Gated Community","Semi Gated","Standalone"),(),"Required canonical source classification. Direct user-labelled evidence wins; registry is consulted only when source evidence is insufficient; absence never implies Standalone."),
("listing_state",PANEL,STAGE_3,("Available","Rented Out","On Hold"),(),"Lifecycle/downstream control; not populated by current Phase-1 path."),
("onboarded_on",PANEL,STAGE_1,(),(),"Onboarding timestamp."),
("raw_message_text",PANEL,STAGE_1,(),(),"Authoritative source text assembled from the canonical intake session; never replaced with persisted Stage-2 values."),
("locality",PANEL,STAGE_2,(),("google_maps_url",),"Explicit Location/Locality/Area source field; verified Maps may replace it later."),
("society_name",PANEL,STAGE_2,(),("locality","google_maps_url"),"Explicit society/community/building first; verified Maps place name next; locality is final deterministic fallback and must be review-flagged."),
("landmark",PANEL,STAGE_2,(),("locality",),"Explicit source landmark first; supported Maps URLs are never stored as landmarks; locality is the final deterministic fallback."),
("pincode",PANEL,STAGE_2,(),("google_maps_url",),"Optional; Maps-owned when verified and non-blocking when unavailable."),
("google_maps_url",PANEL,STAGE_2,(),(),"Deterministically extracted from raw source immediately; runtime expansion/resolution is a later verification step."),
("furnish_type",PANEL,STAGE_2,("Fully Furnished","Semi Furnished"),(),"Exact live Sheet dropdown vocabulary. Unfurnished is represented by blank furnish_type and blank flat_furnishings."),
("BHK",PANEL,STAGE_2,(),(),"Explicit source value, normalized to canonical wording."),
("bathrooms",PANEL,STAGE_2,(),(),"Explicit source value."),
("balconies",PANEL,STAGE_2,(),(),"Explicit source value."),
("floor_number",PANEL,STAGE_2,(),("property_subtype",),"Explicit floor; standalone subtype rule applies."),
("total_floors",PANEL,STAGE_2,(),(),"Explicit source value."),
("built_up_area",PANEL,STAGE_2,(),(),"Explicit source value."),
("carpet_area",PANEL,STAGE_2,(),("built_up_area",),"Explicit source wins; deterministic 90% fallback otherwise."),
("monthly_rent",PANEL,STAGE_2,(),(),"Required for canonical validation."),
("maintenance",PANEL,STAGE_2,(),("maintenance_included",),"Source value; numeric k/lakh normalized, mixed suffixes preserved."),
("maintenance_included",PANEL,STAGE_2,("Yes","No"),(),"Interdependent with maintenance."),
("security_deposit",PANEL,STAGE_2,(),("monthly_rent",),"Explicit amount or explicitly stated months converted using rent."),
("preferred_tenant_type",PANEL,STAGE_2,("Family","Open For All"),(),"Exact live Sheet dropdown vocabulary; deterministic source variants normalized."),
("bachelor_preference",PANEL,STAGE_2,("Female Only ","Male Only","Open for both"),("preferred_tenant_type",),"Exact live Sheet dropdown vocabulary. Family clears this field; Open For All defaults exactly to Open for both unless explicit source evidence overrides it."),
("pet_friendly",PANEL,STAGE_2,("Yes","No"),(),"Explicit no-pet wording -> No; allowed/restricted-pet wording is retained as pet-friendly rather than inventing a prohibition."),
("servant_room",PANEL,STAGE_2,("Yes","No"),(),"Explicit source Yes only; otherwise No."),
("covered_parking",PANEL,STAGE_2,("0","1","2","3","3+"),("internal_property_type",),"Explicit covered-parking count wins; Gated Community/Semi Gated default to 1 when blank."),
("open_parking",PANEL,STAGE_2,(),(),"Explicit numeric source value only; '-' is the deterministic blank sentinel."),
("society_amenities",PANEL,STAGE_2,("Security, Lift, CCTV, Power Backup","Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area","-"),("internal_property_type",),"Exact live Sheet vocabulary; resolved from internal property type when no explicit value exists."),
("flat_furnishings",PANEL,STAGE_2,("Wardrobe, Modular Kitchen, Geyser, Fan, Light","Wardrobe, Modular Kitchen, Geyser, Fan, Light, Fridge, Washing Machine, TV, Sofa, Bed, Dining Table"),("furnish_type",),"Exact live Sheet vocabulary; defaults apply only when blank."),
("property_highlights",PANEL,STAGE_2,(),(),"Explicit source highlights preserved; optional AI beautification may wordsmith later."),
("catalog_title",PANEL,STAGE_2,(),(),"Explicit title preserved; optional AI beautification may wordsmith later."),
("cloudinary_image_urls",PANEL,STAGE_2,(),(),"Separate media process; not required by the deterministic Phase-1 boundary."),
("age_of_property_years",PANEL,STAGE_2,(),(),"Optional source/authoritative fact only; intentional blank is valid."),
("whatsapp_contact_link",PANEL,STAGE_1,(),(),"Fixed company contact link."),
("whatsapp_group_link",PANEL,STAGE_1,(),(),"Fixed company group link."),
("transaction_type",PANEL,STAGE_1,("Rent",),(),"Fixed for current rental workflow."),
("property_subtype",PANEL,STAGE_2,("Apartment","Independent House","Duplex","Independent Floor","Villa","Penthouse","Studio","Farm House"),(),"Explicit source subtype preferred; supported aliases normalize. Apartment is only the normal floor-bearing fallback."),
("city",PANEL,STAGE_1,("Bengaluru",),(),"Fixed for current inventory workflow."),
("posted_url",HOUSING_AGENT,STAGE_3,(),(),"Housing Portal downstream-owned."),
("posted_at",HOUSING_AGENT,STAGE_3,(),(),"Housing Portal downstream-owned."),
("error_notes",HOUSING_AGENT,STAGE_3,(),(),"Housing Portal downstream-owned."),
("meta_catalog_id",META_CATALOG,STAGE_3,(),(),"Meta Catalogue downstream-owned."),
("meta_catalog_status",META_CATALOG,STAGE_3,(),(),"Meta Catalogue downstream-owned."),
("source_group",PANEL,STAGE_1,(),(),"Inbound source/chat identifier."),
("inventory_locked",PANEL,STAGE_3,(),(),"Lifecycle/control field; exact sheet control vocabulary is not verified in repository source."),
]
COLUMNS=tuple(Column(*r) for r in _ROWS)
NAMES=tuple(c.name for c in COLUMNS)
BY_NAME={c.name:c for c in COLUMNS}
GRID_WIDTH=len(COLUMNS); EXPECTED_GRID_WIDTH=48
FIRST_COLUMN="A"; LAST_COLUMN=col_letter(GRID_WIDTH-1); EXPECTED_LAST_COLUMN="AV"
ROW_IDENTITY="listing_id"

def letter(name:str)->str:return BY_NAME[name].letter
def owner_of(name:str)->str:return BY_NAME[name].owner
def stage_of(name:str)->str:return BY_NAME[name].stage
def writable_by(owner:str)->tuple[str,...]:
    if owner not in OWNERS: raise KeyError(owner)
    return tuple(c.name for c in COLUMNS if c.owner==owner)
def assert_writable(owner:str,names:list[str]|tuple[str,...])->None:
    allowed=set(writable_by(owner));unknown=[n for n in names if n not in BY_NAME]
    if unknown:raise KeyError(f"Unknown Housing_Listings field: {', '.join(unknown)}")
    foreign=[n for n in names if n not in allowed]
    if foreign:raise PermissionError(f"{owner} may not write: {', '.join(foreign)}")
def validate_row(values:list[Any]|tuple[Any,...])->tuple[Any,...]:
    if len(values)!=GRID_WIDTH:raise ValueError(f"Housing_Listings row must contain {GRID_WIDTH} values; found {len(values)}")
    return tuple(values)
def row_to_mapping(values:list[Any]|tuple[Any,...])->dict[str,Any]:return dict(zip(NAMES,validate_row(values)))
def mapping_to_row(values:Mapping[str,Any])->list[Any]:
    unknown=[n for n in values if n not in BY_NAME]
    if unknown:raise KeyError(f"Unknown Housing_Listings field: {', '.join(unknown)}")
    return [values.get(n,"") for n in NAMES]
def full_range(first_row:int=1)->str:return f"{FIRST_COLUMN}{first_row}:{LAST_COLUMN}{first_row}"
def range_for(first:str,last:str,row:int)->str:return f"{letter(first)}{row}:{letter(last)}{row}"

def _check()->None:
    assert GRID_WIDTH==EXPECTED_GRID_WIDTH and LAST_COLUMN==EXPECTED_LAST_COLUMN
    assert len(set(NAMES))==48
    expected={"listing_id":"A","raw_message_text":"G","google_maps_url":"L","transaction_type":"AM","property_subtype":"AN","city":"AO","posted_url":"AP","posted_at":"AQ","error_notes":"AR","meta_catalog_id":"AS","meta_catalog_status":"AT","source_group":"AU","inventory_locked":"AV"}
    assert all(letter(k)==v for k,v in expected.items())
    assert writable_by(HOUSING_AGENT)==("posted_url","posted_at","error_notes")
    assert writable_by(META_CATALOG)==("meta_catalog_id","meta_catalog_status")
    assert "Female Only " in BY_NAME["bachelor_preference"].allowed_values
    assert "Female Only" not in BY_NAME["bachelor_preference"].allowed_values
    assert set(BY_NAME["internal_property_type"].allowed_values)=={"Gated Community","Semi Gated","Standalone"}

_check()
