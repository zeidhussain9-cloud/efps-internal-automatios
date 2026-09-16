"""Deterministic validation for the Stage-2 inventory record."""
from __future__ import annotations
import re
from shared.google_sheets import schema
FIXED={"transaction_type":"Rent","city":"Bengaluru","whatsapp_contact_link":"https://wa.me/919148338801","whatsapp_group_link":"https://chat.whatsapp.com/FxOPO0xAOsD6lNwPcIDdFM"}
PROPERTY_TYPES=set(schema.BY_NAME["internal_property_type"].allowed_values)
PROPERTY_SUBTYPES=set(schema.BY_NAME["property_subtype"].allowed_values)
FURNISH_TYPES=set(schema.BY_NAME["furnish_type"].allowed_values)
PREFERRED_TENANT_TYPES=set(schema.BY_NAME["preferred_tenant_type"].allowed_values)
BACHELOR_PREFERENCES=set(schema.BY_NAME["bachelor_preference"].allowed_values)
PET_FRIENDLY=set(schema.BY_NAME["pet_friendly"].allowed_values)
COVERED_PARKING=set(schema.BY_NAME["covered_parking"].allowed_values)
SOCIETY_AMENITIES=set(schema.BY_NAME["society_amenities"].allowed_values)
FURNISHINGS={"AC","Wardrobe","Geyser","Fan","Light","Fridge","TV","Bed","Sofa","Dining Table","Washing Machine","Cupboard","Microwave","Stove","Water Purifier","Gas Pipeline","Chimney","Modular Kitchen"}
NUMERIC={"pincode","built_up_area","carpet_area","age_of_property_years","total_floors","bathrooms","balconies","monthly_rent","security_deposit"}
MAINTENANCE_NON_NUMERIC="Water Charges Additional"
def _numeric(value:object)->bool:return bool(re.fullmatch(r"\d+(?:\.\d+)?",str(value)))
def validate(row:dict)->list[str]:
    errors=[]
    if set(row)!=set(schema.NAMES):return ["row shape does not match canonical 48 fields"]
    for key,value in FIXED.items():
        if row[key]!=value:errors.append(f"{key} must be {value}")
    if row["status"] not in ("Pending","Needs Review"):errors.append("status must be Pending or Needs Review after deterministic extraction")
    if row["intake_status"] not in ("Raw","Processed"):errors.append("intake_status must be Raw or Processed")
    if not row["listing_id"]:errors.append("listing_id required")
    if not row["monthly_rent"]:errors.append("monthly_rent required")
    if row["BHK"] and not re.fullmatch(r"\d+(?:\.\d+)? BHK",str(row["BHK"])) and row["BHK"]!="1 RK":errors.append("invalid BHK")
    if not row["property_subtype"]:errors.append("property_subtype unresolved")
    elif row["property_subtype"] not in PROPERTY_SUBTYPES:errors.append("invalid property_subtype")
    if row["furnish_type"] and row["furnish_type"] not in FURNISH_TYPES:errors.append("invalid furnish_type")
    if row["preferred_tenant_type"] and row["preferred_tenant_type"] not in PREFERRED_TENANT_TYPES:errors.append("invalid preferred_tenant_type")
    if row["bachelor_preference"] and row["bachelor_preference"] not in BACHELOR_PREFERENCES:errors.append("invalid bachelor_preference")
    if row["preferred_tenant_type"]=="Family" and row["bachelor_preference"]:errors.append("bachelor_preference must be blank when preferred_tenant_type is Family")
    elif row["preferred_tenant_type"]=="Open For All" and row["bachelor_preference"] not in BACHELOR_PREFERENCES:errors.append("bachelor_preference must be a canonical value when preferred_tenant_type is Open For All")
    if row["pet_friendly"] and row["pet_friendly"] not in PET_FRIENDLY:errors.append("invalid pet_friendly")
    if row["internal_property_type"] not in PROPERTY_TYPES:errors.append("internal_property_type must be exactly one of Gated Community, Semi Gated, Standalone")
    if row["covered_parking"] not in COVERED_PARKING|{""}:errors.append("invalid covered_parking")
    open_parking=str(row["open_parking"] or "").strip()
    if open_parking and open_parking!="-" and not _numeric(open_parking):errors.append("open_parking must be a numeric explicit count or '-'")
    for key in NUMERIC:
        if row[key] and not _numeric(row[key]):errors.append(f"{key} must be numeric")
    maintenance=str(row["maintenance"]).strip()
    if maintenance and maintenance!=MAINTENANCE_NON_NUMERIC and not re.fullmatch(r"\d+(?: \+ .+)?",maintenance):errors.append("maintenance must be a normalized amount with an optional source qualifier")
    if row["maintenance_included"] not in ("Yes","No",""):errors.append("maintenance_included must be Yes/No/blank")
    if row["maintenance_included"]=="Yes" and maintenance not in {"0",MAINTENANCE_NON_NUMERIC}:errors.append("maintenance must be 0 or Water Charges Additional when included")
    if row["flat_furnishings"]:
        bad=[x.strip() for x in str(row["flat_furnishings"]).split(",") if x.strip() and x.strip() not in FURNISHINGS]
        if bad:errors.append(f"flat_furnishings invalid values: {bad}")
    amenities=str(row["society_amenities"] or "").strip()
    if amenities and amenities not in SOCIETY_AMENITIES:errors.append("society_amenities must match an exact verified Sheet dropdown value")
    for key in ("posted_url","posted_at","error_notes","meta_catalog_id","meta_catalog_status"):
        if row[key]:errors.append(f"{key} must remain empty before downstream stages")
    if any(str(row.get(field,"") or "") for field in schema.RESERVED_COLUMNS):errors.append("reserved Inventory columns AU/AV must remain blank")
    return errors
def validate_raw(row:dict)->list[str]:
    errors=[]
    if set(row)!=set(schema.NAMES):return ["raw row shape does not match canonical 48 fields"]
    if row["status"]!="Raw":errors.append("initial row status must be Raw")
    if row["intake_status"]!="Raw":errors.append("initial row intake_status must be Raw")
    if not row["listing_id"]:errors.append("listing_id required")
    if not row["onboarded_on"]:errors.append("onboarded_on required")
    for key,value in FIXED.items():
        if row[key]!=value:errors.append(f"{key} must be {value}")
    for key in ("listing_state","posted_url","posted_at","error_notes","meta_catalog_id","meta_catalog_status"):
        if row[key]:errors.append(f"{key} must be empty at initial intake")
    if any(str(row.get(field,"") or "") for field in schema.RESERVED_COLUMNS):errors.append("reserved Inventory columns AU/AV must remain blank")
    return errors
