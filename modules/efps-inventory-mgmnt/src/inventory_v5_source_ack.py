"""Staged source acknowledgment preparation and explicit existing-row executor.

No production route calls this module. Completion uses saved upstream output,
live destination/source checks, actual one-attempt HTTP and a durable receipt.
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
                         sealed_source_hash,processed_at,_claimed=None):
    """Prepare exact source status/notes/relation patch; never execute it.

    Source snapshot itself is compared twice, not only its application hash.
    Final state uses saved upstream output plus saved destination conflicts.
    """
    try:instant=datetime.fromisoformat(processed_at.replace('Z','+00:00'))
    except (ValueError,AttributeError):raise IntakeDestinationBlocked('Qualified processed instant required')
    if instant.tzinfo is None:raise IntakeDestinationBlocked('Processed instant must be timezone-qualified')
    saved=_claimed if _claimed is not None else submissions.call('claim_existing',source_page_id)
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
    finally:
        if _claimed is None:submissions.call('release',source_page_id,lease)


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


def complete_existing_source(*,source_page_id,payload_hash,submissions,resolver,
        source_schema_loader,sealed_source_hash,processed_at,workers,notion,
        destination_schema_loader,sealed_destination_hash,source_http):
    """Explicit staged executor. Not called by a production route.

    Uses actual one-attempt HTTP and stored response evidence. Only a durable
    terminal receipt permits restart/readback without another PATCH. Unknown
    dispatch, missing receipt or expired in-flight owner stays held for review.
    """
    try:
        from .inventory_v5_intake_executor import _same
        from .inventory_v5_intake import validate_destination_schema
        from .inventory_v5_intake_binding import active_page
        from .inventory_v5_http import effect_context
    except ImportError:
        from inventory_v5_intake_executor import _same
        from inventory_v5_intake import validate_destination_schema
        from inventory_v5_intake_binding import active_page
        from inventory_v5_http import effect_context
    record=submissions.call('claim_source',source_page_id)
    if not record.get('found') or record.get('busy'):
        return {'status':'held','source_completion_allowed':False}
    lease=record['lease_token'];row_lease=None;page=record['destination_page_id']
    try:
        if record['payload_hash']!=payload_hash:raise IntakeDestinationBlocked('Exact payload required before source completion')
        if record['phase'] not in ('awaiting_source_ack','completed') or record.get('plan') is None:
            raise IntakeDestinationBlocked('Exact destination acknowledgment required')
        plan=record['source_write_plan'] or {'destination_revision':record['plan']['revision']+1}
        row_lease=workers._claim(page,'claim_ack')
        if not row_lease:return {'status':'held','source_completion_allowed':False}
        state=workers.load(page,row_lease)
        expected={**record['plan']['before'],**record['plan']['patch']}
        def quarantine():
            submissions.call('quarantine_source_destination',source_page_id,lease,plan={'row_lease':row_lease,'revision':state['revision']})
        def fresh_destination():
            try:
                schema=destination_schema_loader()
                validate_destination_schema(schema,sealed_schema_hash=sealed_destination_hash)
                if schema!=notion.schema:raise IntakeDestinationBlocked('Destination port schema differs')
                resolver(source_page_id,record['listing_id'],page)
                raw=notion.client.get_page(page)
                if uid(raw.get('id'))!=uid(page):raise IntakeDestinationBlocked('Destination read response identity differs')
                active_page(raw,PARENT)
                current={name:read_notion_value(prop) for name,prop in raw.get('properties',{}).items()
                    if prop.get('type') in ('multi_select','title','rich_text','select','status','checkbox','number','date','url','email','phone_number')}
                current['_edited_at']=raw.get('last_edited_time');current['_archived']=False
                if (state['revision']!=plan['destination_revision'] or state.get('pending_patch') is not None or
                    not _same(state['acknowledged'],expected) or not _same(current,expected)):
                    raise IntakeDestinationBlocked('Live destination differs from frozen acknowledgment')
                return current
            except (ValueError,IntakeDestinationBlocked):
                quarantine()
                raise
        def renew():
            submissions.call('renew',source_page_id,lease);workers.renew(page,row_lease)
        fresh_destination();renew()
        if record['source_write_plan'] is None:
            plan=prepare_source_write(source_page_id=source_page_id,payload_hash=payload_hash,submissions=submissions,
                resolver=resolver,source_schema_loader=source_schema_loader,sealed_source_hash=sealed_source_hash,
                processed_at=processed_at,_claimed=record)
        schema=source_schema_loader();validate_source_schema(schema,sealed_source_hash)
        if schema!=plan['source_schema']:raise IntakeDestinationBlocked('Frozen source schema differs')
        if record['phase']=='completed':
            final=resolver.source(source_page_id,record['listing_id'],page)
            if source_values(final)!=plan['expected_after']:raise IntakeDestinationBlocked('Completed source no longer matches')
            return {'status':plan['status'],'source_completion_allowed':True,'replayed':False}
        if content_hash({'properties':plan['properties']})!=plan['body_hash']:
            raise IntakeDestinationBlocked('Frozen source body hash differs')
        effect=SourceEffectPreparation(submissions,source_page_id,lease)
        saved_effect=record.get('source_effect')
        if saved_effect is None:
            source=resolver.source(source_page_id,record['listing_id'],page)
            if source!=plan['source_before']:raise IntakeDestinationBlocked('Exact source changed before dispatch')
            nonce=effect.begin(source=source,source_schema=schema)['effect_id']
            # Recheck after durable begin; no hash-based stand-in for live values.
            fresh_destination();renew()
            if source_schema_loader()!=schema or resolver.source(source_page_id,record['listing_id'],page)!=source:
                raise IntakeDestinationBlocked('Source/schema changed before HTTP')
            effect.bind(nonce,plan['body_hash'])
            context=effect_context.set(nonce)
            try:receipt=source_http.write_page_with_receipt(source_page_id,deepcopy(plan['properties']))
            finally:effect_context.reset(context)
            effect.receipt(nonce,receipt)
        else:
            # claim_source admits ONLY saved terminal receipts; never resend.
            nonce=saved_effect['effect_id']
        renew();fresh_destination()
        readback=resolver.source(source_page_id,record['listing_id'],page)
        if source_schema_loader()!=schema:raise IntakeDestinationBlocked('Source schema changed after HTTP')
        effect.finish_prepare(nonce,readback)
        # Final live reads and held row lease narrow the race; Notion has no CAS.
        renew();fresh_destination()
        final=resolver.source(source_page_id,record['listing_id'],page)
        if source_values(final)!=source_values(readback) or source_schema_loader()!=schema:
            raise IntakeDestinationBlocked('Source changed before final source commit')
        return submissions.call('source_commit',source_page_id,lease,plan={
            'effect_id':nonce,'readback':source_values(final),'row_lease':row_lease})
    finally:
        try:
            if row_lease:workers.release(page,row_lease)
        finally:
            if lease:submissions.call('release',source_page_id,lease)


def handoff_completed_payload(*,source_page_id,submissions,source_client,
        processed,destination_schema,sealed_destination_hash):
    """Archive a completed version; a current new raw/photo payload owns next.

    This prepares a new submission only. It neither runs processing nor marks
    the new version complete. An old payload cannot be replayed from history.
    """
    try:
        from .inventory_v5_intake_binding import active_page
    except ImportError:
        from inventory_v5_intake_binding import active_page
    saved=submissions.call('claim_source',source_page_id)
    if not saved.get('found') or saved.get('busy'):raise IntakeDestinationBlocked('Completed source required')
    lease=saved['lease_token']
    try:
        source=source_client.get_page(source_page_id);active_page(source,INTAKE_DATABASE_ID)
        if uid(source.get('id'))!=uid(source_page_id):raise IntakeDestinationBlocked('Source response ID differs')
        props=source['properties'];relation=props.get('Processed Property',{})
        if (read_notion_value(props.get('Listing ID',{}))!=saved['listing_id'] or relation.get('has_more') or
            [uid(x.get('id'))for x in relation.get('relation',[])]!=[uid(saved['destination_page_id'])]):
            raise IntakeDestinationBlocked('New payload binding differs')
        payload=source_payload_hash(source)
        candidate=destination_candidate(processed,schema=destination_schema,sealed_schema_hash=sealed_destination_hash)
        if processed.get('listing_id')!=saved['listing_id'] or source_client.get_page(source_page_id)!=source:
            raise IntakeDestinationBlocked('New payload snapshot/identity changed')
        submissions.call('handoff',source_page_id,lease,payload_hash=payload,page_id=saved['destination_page_id'],listing_id=saved['listing_id'],candidate=candidate)
        return {'status':'claimed','payload_hash':payload,'source_completion_allowed':False}
    finally:submissions.call('release',source_page_id,lease)
