"""Deterministic normalization for Stage 2 property processing."""
from __future__ import annotations
import re

FIXED={"transaction_type":"Rent","city":"Bengaluru","whatsapp_contact_link":"https://wa.me/919148338801","whatsapp_group_link":"https://chat.whatsapp.com/FxOPO0xAOsD6lNwPcIDdFM"}
NUMERIC_FIELDS={"pincode","built_up_area","carpet_area","age_of_property_years","total_floors","bathrooms","balconies","open_parking","monthly_rent","security_deposit"}
SEMI_FURNISHED_DEFAULTS=("Wardrobe","Modular Kitchen","Geyser","Fan","Light")
FULLY_FURNISHED_DEFAULTS=SEMI_FURNISHED_DEFAULTS+("Fridge","Washing Machine","TV","Sofa","Bed","Dining Table")
CARPET_RATIO=0.90
PORTAL_SUBTYPE_MAP={"Triplex Villa":"Villa","Complex Villa":"Villa","Villa Complex":"Villa","Triplex":"Independent House","Builder Floor":"Independent Floor","Independent Building":"Independent House"}
NO_FLOOR_SUBTYPES={"Villa","Independent House","Farm House","Duplex"}
STANDALONE_SUBTYPES={"independent house","independent floor","farm house"}
GATED_COMMUNITY_DEFAULTS=("Lift","Gym","CCTV","Power Backup","Swimming Pool","Gated Community","Club House","Garden","Sports","Kids Area","Community Hall")
SEMI_GATED_AMENITIES=("CCTV","Power Backup","Regular Water Supply")
_GATED_KW=re.compile(r"\bgated\s*(?:[:\-]\s*)?(?:community|society)\b",re.I)
_SEMI_GATED_KW=re.compile(r"\bsemi[-\s]*gated\b",re.I)
_STANDALONE_WORDS=re.compile(r"\b(villa|independent house|independent floor|builder floor|farm ?house|duplex|triplex|penthouse|studio)\b",re.I)
_RK_RE=re.compile(r"\b(\d)\s*rk\b",re.I)
_MONTHS=re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(?:months?|mnths?|mos?)\s*$",re.I)
_MAINT_NUMERIC=re.compile(r"^\s*([\d.,]+)\s*(k|l|lakh|lakhs)?\s*(?:\+\s*(.+))?\s*$",re.I)
_UTILITY=re.compile(r"\butilit(?:y|ies)\b",re.I)
_SLACK_LINK=re.compile(r"^<(?P<url>[^|>]+)(\|[^>]*)?>$")

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

def _gating_level_from_text(raw_text:str,row:dict)->str:
    text=str(raw_text or ""); subtype=str(row.get("property_subtype","")).strip().lower()
    if _SEMI_GATED_KW.search(text):return "Semi Gated"
    if _GATED_KW.search(text):return "Gated Community"
    return "Standalone"

def set_internal_type(row:dict,raw_text:str)->dict:
    classification=_gating_level_from_text(raw_text,row); row["internal_property_type"]=classification
    if not str(row.get("society_amenities","")).strip():
        if classification=="Gated Community":row["society_amenities"] = ", ".join(GATED_COMMUNITY_DEFAULTS)
        elif classification=="Semi Gated":row["society_amenities"] = ", ".join(SEMI_GATED_AMENITIES)
        elif str(row.get("property_subtype","")).strip().lower() not in {"","independent house","independent floor","farm house"}:row["society_amenities"] = ", ".join(SEMI_GATED_AMENITIES)
    return row

def apply_tenant_bachelor_rule(row:dict,raw_text:str)->dict:
    tenant=str(row.get("preferred_tenant_type","")).strip().lower()
    if "family" in tenant and "female" in tenant and "bachelor" in tenant:
        row["preferred_tenant_type"]="Open For All"; row["bachelor_preference"]="Female Only"; return row
    if tenant in {"family","family only"}:
        current=str(row.get("bachelor_preference","")).strip()
        if not (current and _verified_in_text(current,raw_text)):row["bachelor_preference"]="Not Allowed"
    return row

def default_property_subtype(row:dict,raw_text:str)->dict:
    if str(row.get("property_subtype","")).strip() or not str(row.get("floor_number","")).strip():return row
    if _STANDALONE_WORDS.search(raw_text or ""):return row
    row["property_subtype"]="Apartment"; return row

def floor_for_standalone(row:dict)->dict:
    subtype=str(row.get("property_subtype","")).strip()
    if subtype in NO_FLOOR_SUBTYPES and not str(row.get("floor_number","")).strip():row["floor_number"]=subtype
    return row

def construct_deterministic_highlights(row:dict,raw_text:str,original_subtype:str)->list[str]:
    fragments=[]
    if _UTILITY.search(raw_text or ""):fragments.append("Utility area")
    if original_subtype and original_subtype in PORTAL_SUBTYPE_MAP:fragments.append(original_subtype)
    floors=[f.strip() for f in str(row.get("floor_number","")).split(",") if f.strip()]
    if len(floors)>=2:fragments.append(f"Multiple units available (floors {', '.join(floors)})")
    match=_RK_RE.search(raw_text or "")
    if match:fragments.append(f"{match.group(1)} RK")
    return list(dict.fromkeys(fragments))

def preserve_rk_wording(row:dict,raw_text:str)->dict:
    match=_RK_RE.search(raw_text or "")
    if not match:return row
    rk_label=f"{match.group(1)} RK"
    for field_name in ("catalog_title","property_highlights"):
        text=str(row.get(field_name,""))
        if not text or rk_label.lower() in text.lower():continue
        row[field_name]=re.sub(r"\bstudio\b",rk_label,text,count=1,flags=re.I) if "studio" in text.lower() else f"{text} ({rk_label})".strip()
    return row

def normalize(row:dict,raw_text:str="")->dict:
    out={k:str(v or "").strip() for k,v in row.items()}
    for key,value in list(out.items()):out[key]=strip_slack_markup(value)
    out.update(FIXED)
    for field in NUMERIC_FIELDS:
        if out.get(field):out[field]=clean_number(out[field])
    if out.get("security_deposit"):out["security_deposit"]=resolve_deposit(row.get("security_deposit",""),out.get("monthly_rent",""))
    if out.get("maintenance"):out["maintenance"]=normalize_maintenance(out["maintenance"])
    if out.get("maintenance_included","").lower()=="yes":out["maintenance_included"]="Yes";out["maintenance"]="0"
    elif out.get("maintenance_included","").lower()=="no":out["maintenance_included"]="No"
    val=out.get("BHK","")
    if val.lower()=="studio" or re.fullmatch(r"1\s*[- ]?\s*rk",val,re.I):out["BHK"]="1 RK"
    else:
        match=re.fullmatch(r"(\d+(?:\.\d+)?)\s*[- ]?\s*bhk",val,re.I)
        if match:out["BHK"]=f"{match.group(1)} BHK"
    original_subtype=out.get("property_subtype","")
    if original_subtype in PORTAL_SUBTYPE_MAP:out["property_subtype"]=PORTAL_SUBTYPE_MAP[original_subtype]
    default_property_subtype(out,raw_text);floor_for_standalone(out)
    if not out.get("flat_furnishings"):
        if out.get("furnish_type")=="Semi Furnished":out["flat_furnishings"]=", ".join(SEMI_FURNISHED_DEFAULTS)
        elif out.get("furnish_type")=="Fully Furnished":out["flat_furnishings"]=", ".join(FULLY_FURNISHED_DEFAULTS)
    if not out.get("carpet_area") and out.get("built_up_area","").isdigit():out["carpet_area"]=str(int(round(int(out["built_up_area"])*CARPET_RATIO)))
    if not out.get("servant_room"):out["servant_room"]="No"
    set_internal_type(out,raw_text);apply_tenant_bachelor_rule(out,raw_text)
    fragments=construct_deterministic_highlights(out,raw_text,original_subtype)
    if fragments and not str(out.get("property_highlights","")).strip():out["property_highlights"]=" | ".join(fragments)
    preserve_rk_wording(out,raw_text)
    return out
