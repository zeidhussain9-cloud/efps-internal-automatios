"""Stage-2 inventory processing and safe Stage-1/2 Sheets persistence."""
from __future__ import annotations
from datetime import datetime, timezone
from shared.google_sheets import schema
from shared.google_sheets.client import GoogleSheetsClient
from shared.google_maps import GoogleMapsClient
from . import extract, normalize, validate, listing_id
from .field_resolution import resolve_internal_property_type

FIXED = {"transaction_type":"Rent","city":"Bengaluru","whatsapp_contact_link":"https://wa.me/919148338801","whatsapp_group_link":"https://chat.whatsapp.com/FxOPO0xAOsD6lNwPcIDdFM"}
PANEL_FIELDS = tuple(name for name in schema.NAMES if schema.owner_of(name) == schema.PANEL)
STAGE_3_PROTECTED = {"listing_state","posted_url","posted_at","error_notes","meta_catalog_id","meta_catalog_status","inventory_locked"}
STAGE_1_2_WRITABLE = tuple(name for name in PANEL_FIELDS if name not in STAGE_3_PROTECTED)
STAGE_2_FIELDS = tuple(name for name in schema.NAMES if schema.stage_of(name) == schema.STAGE_2)


def empty_row() -> dict[str,str]:
    return {name:"" for name in schema.NAMES}


def initial_row(listing_id_value:str, raw_text:str="", source_group:str="", onboarded_on:str="") -> dict[str,str]:
    row=empty_row(); row.update({"listing_id":listing_id_value,"status":"Raw","intake_status":"Raw","onboarded_on":onboarded_on or datetime.now(timezone.utc).isoformat(),"raw_message_text":raw_text,"source_group":source_group,**FIXED}); return row


def _stage2_input_row(row:dict) -> dict:
    out=empty_row()
    for name in ("listing_id","status","intake_status","onboarded_on","raw_message_text","whatsapp_contact_link","whatsapp_group_link","transaction_type","city","source_group"):
        out[name]=str(row.get(name,"") or "")
    out["cloudinary_image_urls"]=str(row.get("cloudinary_image_urls","") or "")
    for name in STAGE_3_PROTECTED:
        out[name]=str(row.get(name,"") or "")
    return out


def deterministic(raw_text:str, row:dict|None=None) -> dict:
    """Stage 2 deterministic projection: source extraction -> resolution -> normalization.

    Existing Stage-2 Sheet values are never deterministic evidence. Raw text is
    the source of truth. Raw Maps URLs are extracted deterministically; Maps
    network enrichment is deliberately performed only by process_closed_session.
    """
    base=_stage2_input_row(row) if row is not None else empty_row()
    base["raw_message_text"]=raw_text or base.get("raw_message_text","")
    base.update(extract.scan(raw_text))
    base["internal_property_type"]=resolve_internal_property_type(raw_text)
    base=normalize.normalize(base,raw_text, resolved_internal_property_type=base["internal_property_type"])
    return base


def process_closed_session(raw_text:str, *, row:dict|None=None, maps_client=None, ai_llm=None):
    out=deterministic(raw_text,row); issues:list[str]=[]; maps=maps_client or GoogleMapsClient(); maps_url=out.get("google_maps_url","") or maps.extract_url(raw_text)
    if maps_url:
        resolved=maps.resolve(maps_url=maps_url)
        if resolved.confidence=="VERIFIED":
            out.update({"google_maps_url":resolved.canonical_url or maps_url,"locality":resolved.locality,"pincode":resolved.pincode})
        elif resolved.confidence in ("PARTIAL_MATCH","NEEDS_RUNTIME_VERIFICATION","NOT_FOUND"):
            issues.append(f"Google Maps verification failed or is incomplete: {resolved.confidence}")
        else:
            issues.append(f"Google Maps resolution returned an unrecognized verification state: {resolved.confidence}")
    # Society-name locality fallback is explicitly last-resort: raw extraction
    # has already run and Maps verification has already had the opportunity to
    # provide a verified locality. Landmark never inherits locality.
    normalize.apply_location_fallbacks(out)
    out["status"]="Pending"; errors=validate.validate(out)
    if errors: out["status"]="Needs Review"; issues.extend(errors)
    if out["status"]=="Pending":
        from .ai import apply
        out=apply(out,raw_text,ai_llm)
        if out.get("_ai_conflicts"): issues.extend(str(x) for x in out["_ai_conflicts"]); out["status"]="Needs Review"; out.pop("_ai_conflicts",None)
    out["intake_status"]="Processed"; return out,issues


def write_new_property(client:GoogleSheetsClient,row:dict):
    validate_errors=validate.validate_raw(row)
    if validate_errors: raise ValueError("Refusing invalid raw inventory row: "+"; ".join(validate_errors))
    schema.assert_writable(schema.PANEL,list(STAGE_1_2_WRITABLE)); return client.append_rows(schema.SHEET_ID,schema.WORKSHEET_NAME,[schema.mapping_to_row(row)])


def write_phase1_update(client:GoogleSheetsClient,row_number:int,row:dict):
    if row_number<2: raise ValueError("inventory row_number must be >= 2")
    if set(row)!=set(schema.NAMES): raise ValueError("inventory row does not match canonical 48-field schema")
    schema.assert_writable(schema.PANEL,list(STAGE_1_2_WRITABLE)); client.write_range(schema.SHEET_ID,schema.WORKSHEET_NAME,schema.range_for("listing_id","internal_property_type",row_number),[[row[name] for name in schema.NAMES[0:4]]]); client.write_range(schema.SHEET_ID,schema.WORKSHEET_NAME,schema.range_for("onboarded_on","city",row_number),[[row[name] for name in schema.NAMES[5:41]]]); client.write_range(schema.SHEET_ID,schema.WORKSHEET_NAME,schema.range_for("source_group","source_group",row_number),[[row["source_group"]]])


def next_listing_id(client:GoogleSheetsClient)->str:
    rows=client.read_range(schema.SHEET_ID,schema.WORKSHEET_NAME,"A2:A"); return listing_id.generate((r[0] for r in rows if r))
