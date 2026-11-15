"""Staged source acknowledgment contract and durable effect preparation.

No source PATCH or ledger completion is executed. Never accepts a new caller
Processed status in place of the saved upstream output and destination checks.
"""
from copy import deepcopy
from datetime import datetime
try:
    from .inventory_v5 import content_hash
    from .inventory_v5_intake import IntakeDestinationBlocked,PARENT,destination_candidate
    from .inventory_v5_intake_binding import source_payload_hash,uid
    from .notion_intake import INTAKE_DATABASE_ID
    from .inventory_v5_adapter import read_notion_value,serialize_notion
except ImportError:
    from inventory_v5 import content_hash
    from inventory_v5_intake import IntakeDestinationBlocked,PARENT,destination_candidate
    from inventory_v5_intake_binding import source_payload_hash,uid
    from notion_intake import INTAKE_DATABASE_ID
    from inventory_v5_adapter import read_notion_value,serialize_notion


def capture_upstream_output(*,source_page_id,payload_hash,processed,issues,submissions,
                            destination_schema,sealed_destination_hash):
    """Freeze the existing pipeline's final output, not a new success request.

    This explicit staged boundary is not wired into production. The caller must
    supply the unmodified output after existing photo/maps/caption checks. A
    future runtime must call it there once, then resume from saved output rather
    than replay extraction/media. No claim of pipeline authorship from a hash.
    """
    if processed.get('status') not in ('Pending','Needs Review') or not isinstance(issues,list) or any(not isinstance(x,str)for x in issues):
        raise IntakeDestinationBlocked('Exact legacy final pipeline output required, not caller Processed')
    candidate=destination_candidate(processed,schema=destination_schema,sealed_schema_hash=sealed_destination_hash)
    saved=submissions.call('claim_existing',source_page_id)
    if not saved.get('found') or saved.get('busy'):raise IntakeDestinationBlocked('Existing source submission required')
    lease=saved['lease_token']
    try:
        if saved['payload_hash']!=payload_hash or saved['candidate']!=candidate:
            raise IntakeDestinationBlocked('Upstream output does not match frozen source payload/candidate')
        outcome={'processed':deepcopy(processed),'issues':deepcopy(issues),'payload_hash':payload_hash,
                 'candidate':candidate,'output_hash':content_hash({'processed':processed,'issues':issues}),
                 'boundary':'existing_pipeline_final_output','source_completion_allowed':False}
        submissions.call('capture_outcome',source_page_id,lease,plan=outcome)
        return outcome
    finally:submissions.call('release',source_page_id,lease)


def validate_source_schema(schema,seal):
    if content_hash(schema)!=seal or len(seal or '')!=64:raise IntakeDestinationBlocked('Reviewed source schema seal differs')
    expected={'Raw Property Data':'rich_text','Photos':'files','Listing ID':'rich_text','Processed Property':'relation',
              'Intake Status':'status','Processing Notes':'rich_text','Processed At':'date'}
    if any(schema.get(k,{}).get('type')!=v for k,v in expected.items()):raise IntakeDestinationBlocked('Source write contract incomplete')
    ids=[v.get('id')for v in schema.values()]
    if any(not x for x in ids) or len(set(ids))!=len(ids):raise IntakeDestinationBlocked('Source stable property IDs required')
    if uid(schema['Processed Property']['relation'].get('database_id'))!=uid(PARENT):raise IntakeDestinationBlocked('Source relation target differs')
    if not {'Processed','Needs Review','Processing'}<={x['name']for x in schema['Intake Status']['status'].get('options',[])}:
        raise IntakeDestinationBlocked('Source processing vocabulary differs')


def source_values(page):
    """Lossless comparison projection for source properties and page binding."""
    values={}
    for name,prop in (page.get('properties') or {}).items():
        kind=prop.get('type')
        if kind in ('title','rich_text','select','status','number','checkbox','url','email','phone_number'):
            values[name]=read_notion_value(prop)
        elif kind=='date':
            date=prop.get('date')
            values[name]=None if date is None else {k:date.get(k)for k in ('start','end','time_zone')}
        elif kind=='relation':
            if prop.get('has_more'):raise IntakeDestinationBlocked('Incomplete source relation readback')
            values[name]=[x['id']for x in prop.get('relation',[])]
        else:
            # Files/dates/unknown read-only values retain their full typed value.
            values[name]=deepcopy(prop.get(kind))
    return {'id':uid(page.get('id')),'parent':deepcopy(page.get('parent')),
            'archived':bool(page.get('archived')or page.get('in_trash')),'values':values}


def prepare_source_write(*,source_page_id,payload_hash,submissions,resolver,source_schema_loader,
                         sealed_source_hash,processed_at):
    """Prepare exact source status/notes/relation patch; never execute it.

    Source snapshot itself is compared twice, not only its application hash.
    Final state uses saved upstream output plus saved destination conflicts.
    """
    try:instant=datetime.fromisoformat(processed_at.replace('Z','+00:00'))
    except (ValueError,AttributeError):raise IntakeDestinationBlocked('Qualified processed instant required')
    if instant.tzinfo is None:raise IntakeDestinationBlocked('Processed instant must be timezone-qualified')
    saved=submissions.call('claim_existing',source_page_id)
    if not saved.get('found') or saved.get('busy'):raise IntakeDestinationBlocked('Source submission absent or busy')
    lease=saved['lease_token']
    try:
        outcome=saved.get('upstream_outcome')
        if saved['phase']!='awaiting_source_ack' or saved['payload_hash']!=payload_hash or not outcome:
            raise IntakeDestinationBlocked('Saved upstream output and exact destination acknowledgment required')
        resolver(source_page_id,saved['listing_id'],saved['destination_page_id'])
        source=resolver.source(source_page_id,saved['listing_id'],saved['destination_page_id'])
        schema=source_schema_loader();validate_source_schema(schema,sealed_source_hash)
        status='Needs Review' if outcome['processed']['status']=='Needs Review' or saved['plan']['conflicts'] else 'Processed'
        issues=outcome['issues']
        note='; '.join(issues) if issues else 'Processed through the canonical EFPS inventory pipeline.'
        existing=read_notion_value(source['properties']['Processing Notes'])
        notes='\n'.join(part for part in (existing.strip(),note.strip())if part)
        properties={'Listing ID':serialize_notion(saved['listing_id'],'rich_text'),
          'Processed Property':{'relation':[{'id':saved['destination_page_id']}]},
          'Intake Status':{'status':{'name':status}},'Processing Notes':serialize_notion(notes,'rich_text'),
          'Processed At':{'date':{'start':processed_at}}}
        if source_schema_loader()!=schema or resolver.source(source_page_id,saved['listing_id'],saved['destination_page_id'])!=source:
            raise IntakeDestinationBlocked('Source exact snapshot/schema changed before preparation')
        expected=source_values(source)
        expected['values'].update({'Listing ID':saved['listing_id'],'Processed Property':[saved['destination_page_id']],
            'Intake Status':status,'Processing Notes':notes,'Processed At':{'start':processed_at,'end':None,'time_zone':None}})
        plan={'body_hash':content_hash({'properties':properties}),'expected_after':expected,'source_before':deepcopy(source),'source_schema':deepcopy(schema),'source_schema_hash':sealed_source_hash,
              'source_before_hash':content_hash(source),'properties':properties,
              'payload_hash':payload_hash,'output_hash':outcome['output_hash'],
              'listing_id':saved['listing_id'],'destination_page_id':saved['destination_page_id'],
              'destination_revision':saved['plan']['revision']+1,'status':status,
              'source_completion_allowed':False,'effect_required':True}
        submissions.call('prepare_source_write',source_page_id,lease,plan=plan)
        return plan
    finally:submissions.call('release',source_page_id,lease)


class SourceEffectPreparation:
    """Durable source effect state port, NOT a source writer or completion port.

    A future executor must call begin on exact fresh reads, bind before HTTP,
    store terminal receipt, read back, then finish_prepare. Unknown flight has
    no automatic recovery path here and blocks fresh source claim.
    """
    def __init__(self,submissions,source_page_id,lease):
        self.submissions=submissions;self.source=source_page_id;self.lease=lease
    def call(self,operation,plan):return self.submissions.call(operation,self.source,self.lease,plan=plan)
    def begin(self,*,source,source_schema):
        return self.call('begin_source_effect',{'source_before':deepcopy(source),'source_schema':deepcopy(source_schema)})
    def bind(self,effect_id,body_hash):
        return self.call('bind_source_dispatch',{'effect_id':effect_id,'method':'PATCH','page_id':self.source,'body_hash':body_hash})
    def receipt(self,effect_id,receipt):
        return self.call('source_receipt',{'effect_id':effect_id,'receipt':deepcopy(receipt)})
    def finish_prepare(self,effect_id,readback):
        return self.call('source_finish_prepare',{'effect_id':effect_id,'readback':source_values(readback)})
