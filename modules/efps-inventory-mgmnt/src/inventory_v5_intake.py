"""Destination-only intake compatibility. Staged, not connected to live intake.

Extraction, captions, media, routing and source processing stay outside this
module. It consumes their existing outputs without changing their behavior.
"""
from copy import deepcopy
import re
try:
    from .inventory_v5 import content_hash, field_equal, AVAILABILITY, PIPELINE, CHANNELS
    from .inventory_v5_adapter import migrate_business_values, serialize_notion
except ImportError:
    from inventory_v5 import content_hash, field_equal, AVAILABILITY, PIPELINE, CHANNELS
    from inventory_v5_adapter import migrate_business_values, serialize_notion

PARENT='bccfd4f55e294b269daa093a928f873a'
# These never gain permission to change from a newly processed source payload.
PROTECTED={'listing_id','onboarded_on','catalog_title','SL number','Availability','Live On',
           'meta_catalog_id','meta_catalog_status','posted_at','posted_url',
           'cloudinary_image_urls','raw_message_text','WhatsApp Group','WhatsApp Destination'}
# Old source/processing status fields are not aliases for canonical business state.
LEGACY_STATUS={'status','intake_status','business_status','listing_state','meta_catalog_status'}
INTERNAL={'notion_page_id','notion_url','notion_edited_at','inventory_contract_version','onboarded_at'}
REQUIRED={'SL number':'title','Availability':'select','Pipeline Status':'select',
          'Live On':'multi_select','_SL numeric sort':'formula','listing_id':'rich_text',
          **{name:'select' for name in ('BHK','furnish_type','flat_furnishings',
            'internal_property_type','society_amenities','preferred_tenant_type',
            'bachelor_preference','property_subtype')}}


class IntakeDestinationBlocked(RuntimeError):
    pass


def validate_destination_schema(schema, *, sealed_schema_hash):
    if not re.fullmatch('[a-f0-9]{64}',sealed_schema_hash or '') or content_hash(schema)!=sealed_schema_hash:
        raise IntakeDestinationBlocked('Fresh reviewed final-schema seal required')
    ids=[v.get('id') for v in schema.values()]
    if any(not x for x in ids) or len(set(ids))!=len(ids):
        raise IntakeDestinationBlocked('Stable unique property IDs required')
    if 'Property' in schema or sum(v.get('type')=='title' for v in schema.values())!=1:
        raise IntakeDestinationBlocked('Exactly one final title required')
    if any(schema.get(k,{}).get('type')!=v for k,v in REQUIRED.items()):
        raise IntakeDestinationBlocked('Final inventory schema is incomplete')
    if schema['_SL numeric sort'].get('formula',{}).get('expression')!='toNumber(prop("SL number"))':
        raise IntakeDestinationBlocked('Numeric title sorting formula differs')
    for field,allowed in [('Availability',AVAILABILITY),('Pipeline Status',PIPELINE),('Live On',CHANNELS)]:
        definition=schema[field]
        if {x['name'] for x in definition[definition['type']].get('options',[])}!=set(allowed):
            raise IntakeDestinationBlocked('Canonical status/channel vocabulary differs: '+field)


def destination_candidate(processed, *, schema, sealed_schema_hash):
    """Map only exact reviewed source enums. Never turn intake status into live state.

    Custom furnishing/amenity lists, unknown tenant/BHK choices, and conflicts
    raise for review. The existing migrate_business_values function is strict;
    it does not silently drop custom details or guess package membership.
    """
    validate_destination_schema(schema,sealed_schema_hash=sealed_schema_hash)
    if not re.fullmatch(r'EF-\d{4}-[0123456789ABCDEFGHJKMNPQRSTVWXYZ]{4}',str(processed.get('listing_id',''))):
        raise IntakeDestinationBlocked('Valid durable listing identity required')
    if any(k in processed for k in ('SL number','Availability','Pipeline Status','Live On')):
        raise IntakeDestinationBlocked('Source payload cannot supply canonical status/title state')
    try:
        mapped=migrate_business_values(deepcopy(processed))
    except ValueError as error:
        raise IntakeDestinationBlocked(str(error)) from error
    out={}
    for field,value in mapped.items():
        if field in LEGACY_STATUS or field in INTERNAL or field.startswith('_'):
            continue
        definition=schema.get(field)
        if definition is None:
            # Unknown nonempty output is not silently discarded.
            if value not in ('',None,[]):
                raise IntakeDestinationBlocked('Unmapped processed field: '+field)
            continue
        kind=definition['type']
        if kind=='formula':continue
        if kind in ('select','status','multi_select'):
            options={x['name'] for x in definition[kind].get('options',[])}
            chosen=value if isinstance(value,list) else [value] if value not in ('',None) else []
            if any(x not in options for x in chosen):
                raise IntakeDestinationBlocked('Unapproved destination option: '+field)
        try:serialize_notion(value,kind)
        except ValueError as error:raise IntakeDestinationBlocked(field+': '+str(error)) from error
        out[field]=value
    # No required title or canonical availability/live state is minted here.
    return out


def existing_destination_plan(*, candidate, current, acknowledged, provenance, listing_id):
    """Narrow patch only where known generated ownership permits replacement.

    Never infer ownership from a match, blank field or freshly extracted data.
    The executor must persist this plan under a lease and exact before-hash;
    this pure plan is NOT an effect or a durable acknowledgment.
    """
    if current.get('_archived'):
        raise IntakeDestinationBlocked('Lifecycle handling required for archived listing')
    if current.get('listing_id')!=listing_id or acknowledged.get('listing_id')!=listing_id:
        raise IntakeDestinationBlocked('Page/listing/acknowledged binding differs')
    keys=(set(current)|set(acknowledged))-{'_edited_at'}
    changed=sorted(k for k in keys if not field_equal(k,current.get(k),acknowledged.get(k)))
    if changed:raise IntakeDestinationBlocked('Unacknowledged owner edits: '+','.join(changed))
    if 'Pipeline Status' in candidate:
        raise IntakeDestinationBlocked('Processed source cannot set canonical pipeline status')
    if current.get('Pipeline Status')=='Removed':
        # A source reprocess is not approval to reactivate or edit a removed
        # listing. Keep lifecycle disposition sticky, even for generated fields.
        changes=[k for k,v in candidate.items() if not field_equal(k,current.get(k),v)]
        if changes:
            raise IntakeDestinationBlocked('Removed listing requires explicit lifecycle decision; no destination update')
    patch={};conflicts=[];next_provenance=deepcopy(provenance)
    for field,value in candidate.items():
        if field_equal(field,current.get(field),value):continue
        if field in PROTECTED:
            conflicts.append(field);continue
        if field in LEGACY_STATUS or field in INTERNAL or field.startswith('_'):
            raise IntakeDestinationBlocked('Source control field cannot enter a destination patch')
        owner=provenance.get(field,{})
        if owner.get('origin')!='derived' or not field_equal(field,current.get(field),owner.get('last_generated_value')):
            conflicts.append(field);continue
        patch[field]=deepcopy(value)
        next_provenance[field]={**owner,'origin':'derived','last_generated_value':deepcopy(value),'derivation_version':5}
    if conflicts:
        # Canonical Pipeline Status is system health. Availability, channel history
        # and original owner data stay unchanged; source completion is separate.
        patch['Pipeline Status']='Needs Review'
    return {'before_hash':content_hash(current),'before':deepcopy(current),
            'patch':patch,'conflicts':sorted(set(conflicts)),
            'provenance':next_provenance,'source_completion_allowed':False,
            'reason':'Durable destination write/readback/mirror/source acknowledgment still required'}
