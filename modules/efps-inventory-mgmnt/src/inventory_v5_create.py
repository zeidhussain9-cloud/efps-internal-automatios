"""Isolated fixture-only new-page controller. No production/source-completion route.

A separate disabled Edge gate is mandatory: current legacy readers would expose
Available drafts despite Processing. No policy here authorizes that exposure.
"""
from copy import deepcopy
from datetime import datetime
try:
    from . import notion_intake,pipeline
    from .inventory_v5 import content_hash,field_equal
    from .inventory_v5_intake import destination_candidate,validate_destination_schema,IntakeDestinationBlocked,PARENT
    from .inventory_v5_intake_binding import active_page,source_payload_hash,uid,INTAKE_DATABASE_ID
    from .inventory_v5_source_ack import source_values
    from .inventory_v5_adapter import read_notion_value,serialize_notion,display_onboarded
    from .inventory_v5_http import effect_context
except ImportError:
    import notion_intake,pipeline
    from inventory_v5 import content_hash,field_equal
    from inventory_v5_intake import destination_candidate,validate_destination_schema,IntakeDestinationBlocked,PARENT
    from inventory_v5_intake_binding import active_page,source_payload_hash,uid,INTAKE_DATABASE_ID
    from inventory_v5_source_ack import source_values
    from inventory_v5_adapter import read_notion_value,serialize_notion,display_onboarded
    from inventory_v5_http import effect_context


class CreateRepository:
    def __init__(self,request):self.request=request
    def call(self,op,source,lease=None,**values):
        return self.request('inventory_v5_create_fixture',worker_operation=op,source_page_id=source,lease=lease,**values)


def empty_relation_source(client,source,payload):
    page=client.get_page(source)
    if uid(page.get('id'))!=uid(source):raise IntakeDestinationBlocked('Source response identity differs')
    active_page(page,INTAKE_DATABASE_ID)
    if source_payload_hash(page)!=payload:raise IntakeDestinationBlocked('Source raw/photos version differs')
    relation=page.get('properties',{}).get('Processed Property',{})
    if relation.get('type')!='relation' or relation.get('has_more') or relation.get('relation')!=[]:
        raise IntakeDestinationBlocked('New source must have a fully read empty relation')
    return page


def identity_pages(client,listing_id):
    pages=[];cursor=None;seen=set()
    while True:
        body={'filter':{'property':'listing_id','rich_text':{'equals':listing_id}},'page_size':100}
        if cursor:body['start_cursor']=cursor
        result=client.request('POST',f'databases/{PARENT}/query',payload=body)
        if not isinstance(result.get('results'),list):raise IntakeDestinationBlocked('Incomplete identity search')
        pages.extend(result['results'])
        if not result.get('has_more'):return pages
        cursor=result.get('next_cursor')
        if not cursor or cursor in seen:raise IntakeDestinationBlocked('Incomplete identity pagination')
        seen.add(cursor)


def typed_created_readback(page,schema,plan,page_id):
    if uid(page.get('id'))!=uid(page_id):raise IntakeDestinationBlocked('Receipt page ID differs from GET')
    active_page(page,PARENT)
    props=page.get('properties',{})
    if set(props)!=set(schema):raise IntakeDestinationBlocked('Full typed created-page schema required')
    for name,definition in schema.items():
        prop=props[name]
        if prop.get('id')!=definition['id'] or prop.get('type')!=definition['type']:
            raise IntakeDestinationBlocked('Created property stable ID/type differs')
        if name in plan['values'] and not field_equal(name,read_notion_value(prop),plan['values'][name]):
            raise IntakeDestinationBlocked('Created page values differ; no ownership bootstrap')
    return source_values(page)


def create_fixture(*,source_page_id,payload_hash,repository,client,http,schema_loader,sealed_schema_hash,
        policy,sealed_policy_hash,onboarded_at,source_schema_loader,sealed_source_hash,pipeline_client,cloudinary,maps_client,ola_client):
    """Reserve -> actual pipeline freeze -> ONE POST -> receipt -> atomic seed.

    Fixture policy is explicit, not a user preference or production policy.
    Title stays blank/Processing until a future coordinated title controller.
    This outcome NEVER acknowledges source completion or links the source row.
    """
    if (not policy or content_hash(policy)!=sealed_policy_hash or policy!={
        'visibility':'isolated_fixture_only','availability':'Available','pipeline':'Processing',
        'live_on':[],'title':'','ownership':'unknown_until_proven'}):
        raise IntakeDestinationBlocked('Sealed isolated fixture policy required; production visibility unresolved')
    try:instant=datetime.fromisoformat(onboarded_at.replace('Z','+00:00'))
    except (ValueError,AttributeError):raise IntakeDestinationBlocked('Frozen qualified onboarding instant required')
    if instant.tzinfo is None:raise IntakeDestinationBlocked('Qualified onboarding instant required')
    schema=schema_loader();validate_destination_schema(schema,sealed_schema_hash=sealed_schema_hash)
    source_schema=source_schema_loader()
    if content_hash(source_schema)!=sealed_source_hash:raise IntakeDestinationBlocked('Source schema seal differs')
    required={'Raw Property Data':'rich_text','Photos':'files','Listing ID':'rich_text','Processed Property':'relation'}
    ids=[p.get('id')for p in source_schema.values()]
    if any(not x for x in ids) or len(set(ids))!=len(ids) or any(source_schema.get(k,{}).get('type')!=v for k,v in required.items()) or uid(source_schema['Processed Property'].get('relation',{}).get('database_id'))!=uid(PARENT):
        raise IntakeDestinationBlocked('Stable new-source schema contract required')
    source=empty_relation_source(client,source_page_id,payload_hash)
    if any(source.get('properties',{}).get(k,{}).get('type')!=v['type'] or source['properties'][k].get('id')!=v['id']for k,v in source_schema.items()):
        raise IntakeDestinationBlocked('Source stable IDs/types differ')
    contract={'destination':schema,'source':source_schema}
    saved=repository.call('claim',source_page_id,payload_hash=payload_hash,value={
        'source_before':source,'schema':contract,'policy':policy,'onboarded_at':onboarded_at})
    if saved.get('held'):return {**saved,'source_completion_allowed':False}
    lease=saved['lease'];listing_id=saved['listing_id']
    def call(op,value=None):return repository.call(op,source_page_id,lease,value=value)
    def fresh():
        call('renew')
        if schema_loader()!=schema or source_schema_loader()!=source_schema or empty_relation_source(client,source_page_id,payload_hash)!=source:
            raise IntakeDestinationBlocked('Frozen source/schema changed; explicit hold, never attach old page')
    try:
        supplied=read_notion_value(source['properties'].get('Listing ID',{}))
        if supplied not in ('',listing_id):raise IntakeDestinationBlocked('Source ID differs from allocated reservation')
        output=saved.get('output');plan=saved.get('plan')
        if output is None:
            fresh()
            if identity_pages(client,listing_id):raise IntakeDestinationBlocked('Allocated ID already exists; no create/adoption')
            call('pipeline_begin')
            row=pipeline.initial_row(listing_id,notion_intake._plain_text(source['properties']['Raw Property Data']),onboarded_at)
            processed,issues=notion_intake.final_intake_output(page=deepcopy(source),listing_id=listing_id,row=row,
                raw_text=row['raw_message_text'],notion=pipeline_client,cloudinary=cloudinary,maps_client=maps_client,ola_client=ola_client)
            fresh();output={'processed':deepcopy(processed),'issues':deepcopy(issues)}
            call('pipeline_output',output)
        if plan is None:
            candidate=destination_candidate(output['processed'],schema=schema,sealed_schema_hash=sealed_schema_hash)
            for field in ('meta_catalog_id','posted_url','posted_at'):
                if candidate.get(field):raise IntakeDestinationBlocked('New page cannot inherit distribution history')
            values={}
            for name,definition in schema.items():
                kind=definition['type']
                if kind in ('formula','rollup','created_time','last_edited_time','created_by','last_edited_by','unique_id','button'):continue
                if kind not in ('rich_text','title','select','status','multi_select','number','checkbox','date','url','email','phone_number'):
                    raise IntakeDestinationBlocked('Unsupported create property requires explicit contract: '+name)
                values[name]=candidate.get(name,[] if kind=='multi_select' else False if kind=='checkbox' else None if kind in ('date','number') else '')
            values.update({'listing_id':listing_id,'SL number':'','Availability':'Available','Pipeline Status':'Processing','Live On':[]})
            if 'onboarded_on' in values:values['onboarded_on']=display_onboarded(instant,display_timezone='Asia/Calcutta')
            body={'parent':{'database_id':PARENT},'properties':{name:serialize_notion(value,schema[name]['type'])for name,value in values.items()}}
            plan={'body':body,'body_hash':content_hash(body),'values':values};call('plan',plan)
        effect=saved.get('effect')
        if effect is None:
            fresh()
            if identity_pages(client,listing_id):raise IntakeDestinationBlocked('Identity appeared before create')
            nonce=call('begin',{'source':source,'schema':contract})['nonce']
            fresh()
            # Zero query results are not an external unique constraint or CAS.
            if identity_pages(client,listing_id):raise IntakeDestinationBlocked('Identity appeared after intent')
            dispatch={'nonce':nonce,'method':'POST','url':'https://api.notion.com/v1/pages',
                'parent':plan['body']['parent'],'body_hash':plan['body_hash']}
            call('dispatch',dispatch)
            context=effect_context.set(nonce)
            try:receipt=http.create_page_with_receipt(deepcopy(plan['body']),dispatch)
            finally:effect_context.reset(context)
            call('receipt',receipt)
            effect={'nonce':nonce,'receipt':receipt}
        receipt=effect['receipt'];page_id=receipt['page_id']
        fresh()
        matches=identity_pages(client,listing_id)
        if len(matches)!=1 or uid(matches[0].get('id'))!=uid(page_id):
            raise IntakeDestinationBlocked('Postreceipt identity is not exactly receipt page; no adoption/bootstrap')
        before=client.get_page(page_id);readback=typed_created_readback(before,schema,plan,page_id)
        # Full response/GET typed projection including readonly properties must
        # agree. Never seed over owner edits hidden outside writable fields.
        if source_values(receipt['body'])!=readback:
            raise IntakeDestinationBlocked('Created page changed since terminal response')
        fresh()
        if typed_created_readback(client.get_page(page_id),schema,plan,page_id)!=readback:
            raise IntakeDestinationBlocked('Owner edit before atomic bootstrap')
        final_matches=identity_pages(client,listing_id)
        if len(final_matches)!=1 or uid(final_matches[0].get('id'))!=uid(page_id):
            raise IntakeDestinationBlocked('Duplicate/binding appeared before bootstrap')
        provenance={name:{'origin':'legacy_unknown','created_value':deepcopy(value),'create_nonce':effect['nonce'],
            'reason':'controller-created value proven, whole-field source/derived lineage unproven'}for name,value in plan['values'].items()}
        mirror={'listing_id':listing_id,'source_kind':'housing_notion','source_tab':'Housing Listings',
            'source_record':{**plan['values'],'notion_page_id':page_id,'inventory_contract_version':5},
            'locality':str(plan['values'].get('locality') or ''),'society_name':str(plan['values'].get('society_name') or ''),
            'bhk':str(plan['values'].get('BHK') or ''),'furnishing':str(plan['values'].get('furnish_type') or ''),
            'monthly_rent':None if plan['values'].get('monthly_rent') in ('',None) else float(plan['values']['monthly_rent']),
            'pet_friendly':str(plan['values'].get('pet_friendly') or ''),
            'cloudinary_image_urls':[x.strip()for x in str(plan['values'].get('cloudinary_image_urls')or'').split(',')if x.strip()],
            'source_hash':content_hash(plan['values']),'inventory_contract_version':5,'inventory_revision':1,
            'availability':'Available','listing_state':'Available','pipeline_status':'Processing','business_status':'Processing',
            'intake_status':'Processing','live_on':[],'onboarded_at':onboarded_at}
        result=call('bootstrap',{'values':plan['values'],'provenance':provenance,'mirror':mirror,'source':source,'schema':contract,'readback':readback})
        return {**result,'listing_id':listing_id,'page_id':page_id,'fixture_only':True,'source_completion_allowed':False}
    finally:call('release')
