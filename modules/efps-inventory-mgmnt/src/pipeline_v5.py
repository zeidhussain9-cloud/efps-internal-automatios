"""Staged v5 pipeline over the audited legacy extractor. No network or writes.

The v4 48-field contract is retained for compatibility until cutover. New names
are additional keys, never silently substituted in the legacy global schema.
"""
from __future__ import annotations
import re
try:
    from . import phase1
    from .inventory_v5 import (AMENITIES, AVAILABILITY, BHK_OPTIONS, FURNISHINGS,
         PACKAGES, balcony_evidence, content_hash, text)
    from .inventory_v5_evidence import evidence_overlay
    from .inventory_v5_adapter import parse_onboarded, display_onboarded, content_readiness
except ImportError:
    import phase1
    from inventory_v5 import (AMENITIES, AVAILABILITY, BHK_OPTIONS, FURNISHINGS,
         PACKAGES, balcony_evidence, content_hash, text)
    from inventory_v5_evidence import evidence_overlay
    from inventory_v5_adapter import parse_onboarded, display_onboarded, content_readiness

DOWNSTREAM = {'listing_id','cloudinary_image_urls','Availability','listing_state','Live On',
              'meta_catalog_id','meta_catalog_status','posted_url','posted_at','onboarded_on'}


def validate_content(row):
    issues=[]
    for field in ('listing_id','monthly_rent','locality','property_subtype','internal_property_type','furnish_type','BHK'):
        if not text(row.get(field)):issues.append(field+' required')
    if row.get('BHK') not in BHK_OPTIONS:issues.append('Unsupported BHK')
    if row.get('furnish_type') not in FURNISHINGS:issues.append('Unsupported furnishing type')
    if row.get('internal_property_type') not in AMENITIES:issues.append('Unsupported internal property type')
    if row.get('preferred_tenant_type') not in ('Family Only','Open For All'):issues.append('Unsupported tenant type')
    elif row['preferred_tenant_type']=='Family Only' and row.get('bachelor_preference')!='-':issues.append('Family Only requires bachelor dash')
    elif row['preferred_tenant_type']=='Open For All' and row.get('bachelor_preference') not in ('','Female Only','Male Only'):issues.append('Invalid explicit gender restriction')
    # Downstream IDs are valid here: bootstrap restrictions are a separate gate.
    return issues


def project(raw, *, existing=None, provenance=None, render_caption, route_bhk):
    existing=existing or {};provenance=provenance or {}
    out=phase1.project(raw,row=existing)
    evidence,source_provenance,issues=evidence_overlay(raw)
    out.update(evidence)
    tenant=text(out.get('preferred_tenant_type'))
    out['preferred_tenant_type']='Family Only' if tenant=='Family' else tenant
    gender=text(out.get('bachelor_preference'))
    out['bachelor_preference']='-' if out['preferred_tenant_type']=='Family Only' else '' if gender=='Open for both' else gender
    out['flat_furnishings']=FURNISHINGS.get(out.get('furnish_type'),'')
    out['society_amenities']=AMENITIES.get(out.get('internal_property_type'),'')
    out['inventory_contract_version']=5
    out['Availability']=existing.get('Availability') or existing.get('listing_state') or 'Available'
    out['Live On']=list(existing.get('Live On',[]))
    conflicts=[]
    # Preserve identities/media/business lifecycle even if raw changes.
    for field in DOWNSTREAM:
        if field in existing:out[field]=existing[field]
    # Protected fields omitted from a real adapter patch as well as retained in
    # this result. Unknown nonblank legacy values are not assumed generated.
    for field,current in existing.items():
        if field in DOWNSTREAM or field not in out:continue
        origin=provenance.get(field,{}).get('origin','legacy_unknown')
        protected=origin=='manual' or (origin=='legacy_unknown' and text(current))
        if protected and out[field]!=current:
            conflicts.append(field);out[field]=current
    derived_provenance = {**provenance, **source_provenance}
    for field in ('flat_furnishings', 'society_amenities', 'bachelor_preference'):
        derived_provenance[field] = {'origin': 'derived', 'last_generated_value': out[field], 'derivation_version': 5}
    for field in conflicts:
        if field in provenance:derived_provenance[field] = dict(provenance[field])
        else:derived_provenance[field] = {'origin': 'legacy_unknown'}
    group,destination=route_bhk(out.get('BHK','')) if out.get('BHK') in BHK_OPTIONS else ('','')
    for field, value in [('WhatsApp Group', group), ('WhatsApp Destination', destination)]:
        old = provenance.get(field, {}).get('origin', 'legacy_unknown')
        if field in existing and (old == 'manual' or (old == 'legacy_unknown' and text(existing[field]))) and existing[field] != value:
            out[field] = existing[field]
            conflicts.append(field)
        else:
            out[field] = value
            derived_provenance[field] = {'origin': 'derived', 'last_generated_value': value, 'derivation_version': 5}
    if not group:issues.append('Invalid BHK route; distribution disabled')
    issues.extend(validate_content(out))
    if out['Availability'] not in AVAILABILITY:issues.append('Unsupported availability')
    if existing.get('onboarded_on'):
        try:
            instant=parse_onboarded(existing['onboarded_on'],legacy_timezone='Asia/Calcutta')
            out['onboarded_at']=instant.isoformat()
            # Only ISO display offenders change; old readable text is retained.
            if re.match(r'^\d{4}-\d{2}-\d{2}T', existing['onboarded_on']):out['onboarded_on']=display_onboarded(instant,display_timezone='Asia/Calcutta')
        except ValueError as error:issues.append(str(error))
    caption=render_caption(out,raw)
    caption_origin=provenance.get('whatsapp_post',{}).get('origin','legacy_unknown')
    if existing.get('whatsapp_post') and caption_origin!='derived':
        out['whatsapp_post']=existing['whatsapp_post']
        if caption!=existing['whatsapp_post']:conflicts.append('whatsapp_post')
    else:out['whatsapp_post']=caption
    issues.extend('Protected manual/legacy conflict: '+field for field in sorted(set(conflicts)))
    out['Pipeline Status'],issues=content_readiness(out,issues,route_valid=bool(group))
    if existing.get('Pipeline Status')=='Removed':out['Pipeline Status']='Removed'
    return {'row':out,'provenance':derived_provenance,'issues':issues,'conflicts':sorted(set(conflicts)),
       'contract_version':5,'source_hash':content_hash({'raw':raw,'version':5})}
