"""Canonical deterministic Phase-1 inventory boundary."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import re
from shared.google_maps import GoogleMapsClient
from shared.google_sheets import schema
try:
    from . import extract, normalize, validate
    from .field_resolution import resolve_internal_property_type, resolve_property_subtype, has_property_subtype_evidence
    from .source_segments import split_source_messages
except ImportError:
    import extract, normalize, validate
    from field_resolution import resolve_internal_property_type, resolve_property_subtype, has_property_subtype_evidence
    from source_segments import split_source_messages

CANONICAL_PROPERTY_TYPES=("Gated Community","Semi Gated","Standalone")
GATED_AMENITIES="Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area"
SEMI_GATED_AMENITIES="Security, Lift, CCTV, Power Backup"
STANDALONE_AMENITIES="-"
PLACEHOLDERS={"","-","—","n/a","na","none","nil","not available","not mentioned"}

@dataclass(frozen=True)
class Phase1Result:
    row:dict[str,str]; issues:tuple[str,...]; report:dict[str,Any]

def apply_location_contract(row:dict[str,str])->dict[str,bool]:
    locality=str(row.get("locality","") or "").strip(); landmark=str(row.get("landmark","") or "").strip(); society=str(row.get("society_name","") or "").strip()
    if GoogleMapsClient.is_maps_url(landmark): row["landmark"]="";landmark=""
    if not landmark and locality:row["landmark"]=locality
    society_fallback=False
    if society.lower() in PLACEHOLDERS:society=""
    if not society and locality:row["society_name"]=locality;society_fallback=True
    return {"society_name_locality_fallback":society_fallback}

def resolve_parking_society_amenities(row:dict[str,str])->dict[str,str]:
    property_type=str(row.get("internal_property_type","") or "").strip();covered=str(row.get("covered_parking","") or "").strip();open_parking=str(row.get("open_parking","") or "").strip()
    if property_type in {"Gated Community","Semi Gated"} and not covered:covered="1"
    if not open_parking:open_parking="-"
    amenities=str(row.get("society_amenities","") or "").strip()
    if not amenities:amenities=GATED_AMENITIES if property_type=="Gated Community" else SEMI_GATED_AMENITIES if property_type=="Semi Gated" else STANDALONE_AMENITIES if property_type=="Standalone" else ""
    return {"internal_property_type":property_type,"covered_parking":covered,"open_parking":open_parking,"society_amenities":amenities}

def _report(row,issues,flags,trace):
    return {"populated_fields":[n for n in schema.NAMES if str(row.get(n,"") or "").strip()],"blank_fields":[n for n in schema.NAMES if not str(row.get(n,"") or "").strip()],"unresolved_fields":[n for n in ("internal_property_type","locality","property_subtype") if not str(row.get(n,"") or "").strip()],"review_flags":flags,"issues":list(issues),"trace":trace}

def project(raw_text:str,row:dict[str,Any]|None=None)->dict[str,str]:
    base={n:"" for n in schema.NAMES}
    if row:
        for name in ("listing_id","status","intake_status","onboarded_on","raw_message_text","whatsapp_contact_link","whatsapp_group_link","transaction_type","city","source_group","cloudinary_image_urls","listing_state","posted_url","posted_at","error_notes","meta_catalog_id","meta_catalog_status","inventory_locked"):
            base[name]=str(row.get(name,"") or "")
    base["raw_message_text"]=raw_text or base.get("raw_message_text","")
    base.update({n:v for n,v in extract.scan(raw_text).items() if n in schema.BY_NAME})
    base["internal_property_type"]=resolve_internal_property_type(raw_text)
    base=normalize.normalize(base,raw_text,resolved_internal_property_type=base["internal_property_type"])
    resolved_subtype=resolve_property_subtype(raw_text)
    if resolved_subtype:
        base["property_subtype"]=resolved_subtype
    elif has_property_subtype_evidence(raw_text):
        base["property_subtype"]=""
    base.update(resolve_parking_society_amenities(base));maps_url=GoogleMapsClient.extract_url(raw_text)
    if maps_url:base["google_maps_url"]=maps_url
    apply_location_contract(base)
    if set(base)!=set(schema.NAMES):raise ValueError("Phase-1 projection must contain exactly 48 fields")
    return base

def run_phase1(raw_text:str,*,row:dict[str,Any]|None=None)->Phase1Result:
    projected=project(raw_text,row=row);projected["status"]="Pending";projected["intake_status"]="Processed";issues=validate.validate(projected)
    if issues:projected["status"]="Needs Review"
    extracted=extract.scan(raw_text);flags=[]
    if projected.get("society_name","").strip()==projected.get("locality","").strip() and not str(extracted.get("society_name","") or "").strip():flags.append("society_name_locality_fallback")
    if not projected.get("internal_property_type","").strip():flags.append("internal_property_type_unresolved")
    if not projected.get("property_subtype","").strip():flags.append("property_subtype_unresolved")
    trace={"source_segments":split_source_messages(raw_text),"extracted_candidates":extracted,"resolved":{n:projected.get(n,"") for n in ("BHK","maintenance","maintenance_included","internal_property_type","property_subtype","google_maps_url")}}
    return Phase1Result(projected,tuple(issues),_report(projected,issues,flags,trace))
