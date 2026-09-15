"""Deterministic normalization for Stage 2 property processing."""
from __future__ import annotations
import re

FIXED={"transaction_type":"Rent","city":"Bengaluru","whatsapp_contact_link":"https://wa.me/919148338801","whatsapp_group_link":"https://chat.whatsapp.com/FxOPO0xAOsD6lNwPcIDdFM"}
NUMERIC_FIELDS={"pincode","built_up_area","carpet_area","age_of_property_years","total_floors","bathrooms","balconies","open_parking","monthly_rent","security_deposit"}
SEMI_FURNISHED_DEFAULTS=("Wardrobe","Modular Kitchen","Geyser","Fan","Light")
FULLY_FURNISHED_DEFAULTS=SEMI_FURNISHED_DEFAULTS+("Fridge","Washing Machine","TV","Sofa","Bed","Dining Table")
CARPET_RATIO=0.90
PORTAL_SUBTYPE_MAP={"Triplex Villa":"Villa","Complex Villa":"Villa","Villa Complex":"Villa","Duplex Villa":"Villa","Triplex":"Independent House","Builder Floor":"Independent Floor","Independent Building":"Independent House"}
NO_FLOOR_SUBTYPES={"Villa","Independent House","Farm House","Duplex"}
GATED_COMMUNITY_DEFAULTS=("Club House","Lift","Gym","CCTV","Power Backup","Swimming Pool","Garden","Sports","Kids Area")
SEMI_GATED_AMENITIES=("Security","Lift","CCTV","Power Backup")
STANDALONE_AMENITIES=("-")
_RK_RE=re.compile(r"\b(\d)\s*rk\b",re.I)
_MONTHS=re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(?:months?|mnths?|mos?)\s*$",re.I)
_MAINT_NUMERIC=re.compile(r"^\s*([\d.,]+)\s*(k|l|lakh|lakhs)?\s*(?:\+\s*(.+))?\s*$",re.I)
_UTILITY=re.compile(r"\butilit(?:y|ies)\b",re.I)
_SLACK_LINK=re.compile(r"^<(?P<url>[^|>]+)(\|[^>]*)?>$")
_PLACEHOLDERS={"*","-","—","n/a","na","none","not available","not mentioned","nil"}
_YES_VALUES={"yes","y","true","1","allowed"}
_NO_VALUES={"no","n","false","0","not allowed","not permitted","none"}
_STANDALONE_WORDS=re.compile(r"\b(independent\s+house|independent\s+floor|builder\s+floor|farm ?house|stand[-\s]*alone)\b",re.I)


def strip_slack_markup(value:str)->str:
    match=_SLACK_LINK.match(str(value or "").strip()); return match.group("url").strip() if match else str(value or "").strip()


def clean_number(value:str)->str:
    raw=str(value or "").strip()
    if not raw:return ""
    cleaned=re.sub(r"[₹,\s]","",raw)
    cleaned=re.sub(r"(?:sq\.?\s*ft\.?|sqft|sft|rs\.?|inr)","",cleaned,flags=re.I)
    return cleaned.rstrip("0").rstrip(".") if "." in cleaned and re.fullmatch(r"\d+(?:\.\d+)?",cleaned) else cleaned if re.fullmatch(r"\d+(?:\.\d+)?",cleaned) else raw


def normalize_maintenance(value:str)->str:
    raw=str(value or "").strip()
    if not raw:return ""
    if raw.lower()=="included":return "0"
    if re.fullmatch(r"included\s*\+\s*(?:water|water\s*charges?)",raw,re.I):return "Water Charges Additional"
    if re.fullmatch(r"0\s*\+\s*(?:water|water\s*charges?)",raw,re.I):return "Water Charges Additional"
    m=_MAINT_NUMERIC.fullmatch(raw)
    if not m:return re.sub(r"(?<=\d),(?=\d)","",raw)
    n=float(m.group(1).replace(",","")); unit=(m.group(2) or "").lower()
    if unit=="k":n*=1000
    elif unit in {"l","lakh","lakhs"}:n*=100000
    result=str(int(n)); suffix=(m.group(3) or "").strip()
    return f"{result} + {suffix}" if suffix else result


def resolve_deposit(value:str,monthly_rent:str)->str:
    raw=str(value or "").strip()
    if not raw:return ""
    m=_MONTHS.match(raw)
    if not m:return clean_number(raw)
    rent=clean_number(monthly_rent)
    return str(int(float(m.group(1))*float(rent))) if re.fullmatch(r"\d+(?:\.\d+)?",rent) else raw


def _verified_in_text(value:str,raw_text:str)->bool:
    def norm(text:str)->str:return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9 ]"," ",str(text or "").lower())).strip()
    needle=norm(value); return bool(needle) and needle in norm(raw_text)


def _usable(value:str)->bool:
    return bool(str(value or "").strip()) and str(value or "").strip().lower() not in _PLACEHOLDERS


def _canonical_tenant(value:str)->str:
    raw=str(value or "").strip().lower()
    if not raw:return ""
    if raw in {"anyone","anybody","open for all","all","all tenants","everyone"}:return "Open For All"
    if "family" in raw:return "Family"
    return "Open For All" if raw in {"open","open tenant"} else value.strip()


def _pet_value(raw_text:str)->str:
    text=str(raw_text or "")
    if re.search(r"\b(?:pets?|animals?)\s*(?:are\s*)?(?:not\s*allowed|not\s*permitted|prohibited|banned)\b",text,re.I):return "No"
    if re.search(r"\b(?:no|without)\s+pets?\b",text,re.I):return "No"
    return "Yes"


def _canonical_subtype(value:str)->str:
    raw=str(value or "").strip()
    if not raw:return ""
    for key, canonical in PORTAL_SUBTYPE_MAP.items():
        if raw.lower()==key.lower():return canonical
    for canonical in ("Apartment","Independent House","Duplex","Independent Floor","Villa","Penthouse","Studio","Farm House"):
        if raw.lower()==canonical.lower():return canonical
    return raw


def default_property_subtype(row:dict,raw_text:str)->dict:
    explicit=_canonical_subtype(row.get("property_subtype","")); row["property_subtype"]=explicit
    if explicit:return row
    # Operational EFPS subtype usage: Apartment is the normal building/flat
    # selection; Villa is used for villas; Studio is reserved for 1 RK.
    if re.search(r"\b1\s*[- ]?\s*rk\b",raw_text or "",re.I):row["property_subtype"]="Studio"
    elif re.search(r"\b(?:duplex\s+)?villa\b",raw_text or "",re.I):row["property_subtype"]="Villa"
    elif _STANDALONE_WORDS.search(raw_text or ""):
        return row
    else:row["property_subtype"]="Apartment"
    return row


def floor_for_standalone(row:dict)->dict:
    subtype=str(row.get("property_subtype","")).strip()
    if subtype in NO_FLOOR_SUBTYPES and not str(row.get("floor_number","")).strip():row["floor_number"]=subtype
    return row


def _fallback_location(row:dict)->str:
    return str(row.get("locality","")).strip()


def apply_location_fallbacks(row:dict)->dict:
    # Society fallback is intentionally last-resort and runs only after raw
    # extraction and Maps enrichment have had an opportunity to find a name.
    # Landmark never inherits locality.
    location=_fallback_location(row)
    if not _usable(row.get("society_name","")) and location:row["society_name"]=location
    return row


def apply_parking_defaults(row:dict)->dict:
    if row.get("internal_property_type") in {"Gated Community","Semi Gated"} and not str(row.get("covered_parking","")).strip():row["covered_parking"]="1"
    return row


def apply_tenant_bachelor_rule(row:dict,raw_text:str)->dict:
    tenant=_canonical_tenant(row.get("preferred_tenant_type",""))
    row["preferred_tenant_type"]=tenant
    lower_raw=str(raw_text or "").lower()
    if ("family" in lower_raw and "female" in lower_raw and "bachelor" in lower_raw) or re.search(r"\bfamily\s*&\s*female\b",lower_raw):
        row["preferred_tenant_type"]="Open For All"; row["bachelor_preference"]="Female Only "; return row
    current=str(row.get("bachelor_preference","")).strip()
    if current and not _verified_in_text(current,raw_text):current=""
    if current:row["bachelor_preference"]=current
    elif tenant=="Family":row["bachelor_preference"]=""
    return row


def normalize_bachelor_preference(row:dict)->dict:
    value=str(row.get("bachelor_preference","")).strip().lower()
    if value=="female only":row["bachelor_preference"]="Female Only "
    elif value=="male only":row["bachelor_preference"]="Male Only"
    elif value=="open for both":row["bachelor_preference"]="Open for both"
    return row


def construct_deterministic_highlights(row:dict,raw_text:str,original_subtype:str)->list[str]:
    fragments=[]; explicit=str(row.get("property_highlights","")).strip()
    if _usable(explicit):return [explicit]
    if _UTILITY.search(raw_text or ""):fragments.append("Utility area")
    if original_subtype and original_subtype in PORTAL_SUBTYPE_MAP:fragments.append(original_subtype)
    floors=[f.strip() for f in str(row.get("floor_number","")).split(",") if f.strip()]
    if len(floors)>=2:fragments.append(f"Multiple units available (floors {', '.join(floors)})")
    match=_RK_RE.search(raw_text or "")
    if match:fragments.append(f"{match.group(1)} RK")
    return list(dict.fromkeys(fragments))


def build_catalog_title(row:dict)->str:
    if _usable(row.get("catalog_title","")):return str(row["catalog_title"]).strip()
    parts=[]; furnish=str(row.get("furnish_type","")).strip(); bhk=str(row.get("BHK","")).strip(); location=str(row.get("locality","")).strip()
    if furnish:parts.append(furnish)
    if bhk:parts.append(bhk)
    title=" ".join(parts)+" for Rent" if parts else "Property for Rent"
    return f"{title} - {location}" if location else title


def preserve_rk_wording(row:dict,raw_text:str)->dict:
    match=_RK_RE.search(raw_text or "")
    if not match:return row
    rk_label=f"{match.group(1)} RK"
    for field_name in ("catalog_title","property_highlights"):
        text=str(row.get(field_name,""))
        if not text or rk_label.lower() in text.lower():continue
        row[field_name]=re.sub(r"\bstudio\b",rk_label,text,count=1,flags=re.I) if "studio" in text.lower() else f"{text} ({rk_label})".strip()
    return row


def normalize(row:dict,raw_text:str="",*,resolved_internal_property_type:str="")->dict:
    out={k:str(v or "").strip() for k,v in row.items()}
    for field,value in list(out.items()):
        out[field]=strip_slack_markup(value)
        if field in {"society_name","landmark","locality","internal_property_type","property_subtype","property_highlights","catalog_title"}:
            out[field]=out[field].strip("*_")
    out.update(FIXED)
    for field in NUMERIC_FIELDS:
        if out.get(field):out[field]=clean_number(out[field])
    if out.get("security_deposit"):out["security_deposit"]=resolve_deposit(row.get("security_deposit",""),out.get("monthly_rent",""))
    if out.get("maintenance"):out["maintenance"]=normalize_maintenance(out["maintenance"])
    if out.get("maintenance_included","").lower()=="yes":
        out["maintenance_included"]="Yes"
        if out.get("maintenance","").strip().lower() in {"included","included + water","included + water charges","0 + water","0 + water charges"}:
            out["maintenance"]="Water Charges Additional" if "water" in out["maintenance"].lower() else "0"
        elif not out.get("maintenance"):
            out["maintenance"]="0"
    elif out.get("maintenance_included","").lower()=="no":out["maintenance_included"]="No"
    val=out.get("BHK","")
    if val.lower()=="studio" or re.fullmatch(r"1\s*[- ]?\s*rk",val,re.I):out["BHK"]="1 RK"
    else:
        match=re.fullmatch(r"(\d+(?:\.\d+)?)\s*[- ]?\s*bhk",val,re.I)
        if match:out["BHK"]=f"{match.group(1)} BHK"
    original_subtype=out.get("property_subtype","")
    default_property_subtype(out,raw_text);floor_for_standalone(out)
    if not out.get("flat_furnishings"):
        if out.get("furnish_type")=="Semi Furnished":out["flat_furnishings"]=", ".join(SEMI_FURNISHED_DEFAULTS)
        elif out.get("furnish_type")=="Fully Furnished":out["flat_furnishings"]=", ".join(FULLY_FURNISHED_DEFAULTS)
    if not out.get("carpet_area") and out.get("built_up_area","").isdigit():out["carpet_area"]=str(int(round(int(out["built_up_area"])*CARPET_RATIO)))
    if not out.get("servant_room"):out["servant_room"]="No"
    if resolved_internal_property_type not in {"Gated Community","Semi Gated","Standalone"}:
        raise ValueError("normalize requires canonical resolved_internal_property_type")
    out["internal_property_type"]=resolved_internal_property_type
    if not _usable(out.get("society_amenities","")):
        out["society_amenities"]=("Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area" if resolved_internal_property_type=="Gated Community" else "Security, Lift, CCTV, Power Backup" if resolved_internal_property_type=="Semi Gated" else "-")
    apply_parking_defaults(out)
    out["pet_friendly"]=_pet_value(raw_text)
    apply_tenant_bachelor_rule(out,raw_text);normalize_bachelor_preference(out)
    fragments=construct_deterministic_highlights(out,raw_text,original_subtype)
    if fragments and not _usable(out.get("property_highlights","")):out["property_highlights"]=" | ".join(fragments)
    if not _usable(out.get("catalog_title","")):out["catalog_title"]=build_catalog_title(out)
    preserve_rk_wording(out,raw_text)
    return out
