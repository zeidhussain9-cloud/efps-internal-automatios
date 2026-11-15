"""Read-only existing intake binding resolver and source-ack preparation.

No create, PATCH, source completion, extraction, media upload or routing effects.
"""
from copy import deepcopy
import re
try:
    from .inventory_v5 import content_hash
    from .inventory_v5_intake import IntakeDestinationBlocked,PARENT
    from .inventory_v5_adapter import read_notion_value
    from .notion_intake import INTAKE_DATABASE_ID,_photos,_file_url
except ImportError:
    from inventory_v5 import content_hash
    from inventory_v5_intake import IntakeDestinationBlocked,PARENT
    from inventory_v5_adapter import read_notion_value
    from notion_intake import INTAKE_DATABASE_ID,_photos,_file_url
from urllib.parse import urlparse
import hashlib,json


def uid(value):return str(value or '').replace('-','').lower()


def active_page(page,parent):
    p=page.get('parent') or {}
    if page.get('archived') or page.get('in_trash') or uid(p.get('database_id') or p.get('data_source_id'))!=uid(parent):
        raise IntakeDestinationBlocked('Page is not active in its required parent')


def source_payload_hash(page):
    props=page.get('properties') or {}
    raw=read_notion_value(props.get('Raw Property Data') or {})
    if not raw:raise IntakeDestinationBlocked('Raw source text missing')
    # Exactly the existing intake claim hash, not a new photo/media algorithm.
    photos=[{'type':x.get('type'),'name':x.get('name'),'path':urlparse(_file_url(x)).path}for x in _photos(page)]
    return hashlib.sha256(json.dumps({'raw':raw,'photos':photos},sort_keys=True).encode()).hexdigest()


class ExistingBindingResolver:
    def __init__(self,*,client,request,payload_hash):
        self.client=client;self.request=request;self.payload_hash=payload_hash

    def source(self,source_page_id,listing_id,destination_page_id):
        page=self.client.get_page(source_page_id)
        if uid(page.get('id'))!=uid(source_page_id):raise IntakeDestinationBlocked('Source response identity mismatch')
        active_page(page,INTAKE_DATABASE_ID)
        if source_payload_hash(page)!=self.payload_hash:raise IntakeDestinationBlocked('Source payload version changed')
        props=page.get('properties') or {}
        if read_notion_value(props.get('Listing ID') or {})!=listing_id:
            raise IntakeDestinationBlocked('Source Listing ID differs from durable binding')
        relation=props.get('Processed Property') or {}
        if relation.get('type')!='relation' or relation.get('has_more') or len(relation.get('relation',[]))!=1 or {uid(x.get('id'))for x in relation.get('relation',[])}!={uid(destination_page_id)}:
            raise IntakeDestinationBlocked('Exact single existing source relation required')
        return page

    def __call__(self,source_page_id,listing_id,page_id):
        if not re.fullmatch(r'EF-\d{4}-[0123456789ABCDEFGHJKMNPQRSTVWXYZ]{4}',listing_id or ''):
            raise IntakeDestinationBlocked('Invalid binding identity')
        known=self.request('inventory_v5_intake_binding',source_page_id=source_page_id)
        if known!={'found':True,'source_page_id':source_page_id,'listing_id':listing_id,'page_id':page_id,'payload_hash':self.payload_hash,'active':True}:
            raise IntakeDestinationBlocked('Durable existing source/destination binding differs')
        source=self.source(source_page_id,listing_id,page_id)
        rows=[];cursor=None;seen=set()
        while True:
            body={'filter':{'property':'listing_id','rich_text':{'equals':listing_id}},'page_size':100}
            if cursor:body['start_cursor']=cursor
            result=self.client.request('POST',f'databases/{PARENT}/query',payload=body)
            batch=result.get('results')
            if not isinstance(batch,list):raise IntakeDestinationBlocked('Invalid destination identity query')
            rows.extend(batch)
            if len(rows)>1:raise IntakeDestinationBlocked('Multiple destinations share listing identity')
            if not result.get('has_more'):break
            cursor=result.get('next_cursor')
            if not cursor or cursor in seen:raise IntakeDestinationBlocked('Incomplete/cyclic destination identity query')
            seen.add(cursor)
        if len(rows)!=1 or uid(rows[0].get('id'))!=uid(page_id):
            raise IntakeDestinationBlocked('Unique destination page not found')
        active_page(rows[0],PARENT)
        if read_notion_value((rows[0].get('properties')or{}).get('listing_id')or{})!=listing_id:
            raise IntakeDestinationBlocked('Destination query returned mismatching identity')
        # Re-read source after pagination so changed source content/relation is
        # not hidden by a successful earlier read. This is not atomic CAS.
        if self.source(source_page_id,listing_id,page_id)!=source:
            raise IntakeDestinationBlocked('Source changed during binding lookup')
        return {'source_page_id':source_page_id,'listing_id':listing_id,'page_id':page_id,'active':True,'unique':True}


def prepare_source_ack(*,source_page_id,payload_hash,processed,submissions,resolver):
    """Durably prepare the source relation only after exact destination ack.

    SQL checks the destination row/mirror revision again. No source PATCH or
    processed status is sent, and later source versions remain blocked.
    """
    saved=submissions.call('claim_existing',source_page_id)
    if not saved.get('found') or saved.get('busy'):
        raise IntakeDestinationBlocked('Existing submission is absent or busy')
    lease=saved['lease_token']
    try:
        if saved['phase']!='awaiting_source_ack' or saved['payload_hash']!=payload_hash or saved['listing_id']!=processed.get('listing_id'):
            raise IntakeDestinationBlocked('Exact awaiting-source-ack submission required')
        resolver(source_page_id,saved['listing_id'],saved['destination_page_id'])
        source=resolver.source(source_page_id,saved['listing_id'],saved['destination_page_id'])
        # This ledger has not yet captured the upstream processing outcome.
        # Never trust a fresh caller status to manufacture Processed success.
        database=resolver.client.request('GET',f'databases/{INTAKE_DATABASE_ID}')
        definitions=database.get('properties') or {}
        for name,kind in [('Listing ID','rich_text'),('Processed Property','relation'),('Intake Status','status')]:
            if definitions.get(name,{}).get('type')!=kind:
                raise IntakeDestinationBlocked('Source acknowledgment schema differs: '+name)
        allowed={x['name']for x in definitions['Intake Status']['status'].get('options',[])}
        relation=definitions['Processed Property']['relation']
        if not {'Processed','Needs Review'}<=allowed or uid(relation.get('database_id'))!=uid(PARENT):
            raise IntakeDestinationBlocked('Source status/relation contract differs')
        plan={'source_before':deepcopy(source),'source_before_hash':content_hash(source),
              'payload_hash':payload_hash,'destination_revision':saved['plan']['revision']+1,
              'destination_page_id':saved['destination_page_id'],'listing_id':saved['listing_id'],
              'properties':{'Listing ID':{'rich_text':[{'type':'text','text':{'content':saved['listing_id']}}]},
                 'Processed Property':{'relation':[{'id':saved['destination_page_id']}]}},
              'source_status_unresolved':True,'source_completion_allowed':False}
        submissions.call('prepare_source_ack',source_page_id,lease,plan=plan)
        return plan
    finally:submissions.call('release',source_page_id,lease)
