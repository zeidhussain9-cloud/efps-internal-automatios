from copy import deepcopy
import re
import pytest
from test_inventory_v5_full_ports import DB,PAGE
from test_inventory_v5_intake_executor import SOURCE
from test_inventory_v5_intake import fixture
from src.inventory_v5_create import create_fixture,CreateRepository
from src.inventory_v5_http import V5HttpNotionClient
from src.inventory_v5 import content_hash
from src.inventory_v5_intake import PARENT,IntakeDestinationBlocked
from src.inventory_v5_intake_binding import INTAKE_DATABASE_ID,source_payload_hash
from src.inventory_v5_adapter import serialize_notion

@pytest.fixture
def db():
    value=DB();yield value;value.close()


def setup(db,monkeypatch):
    from src import notion_intake
    processed,schema=fixture()
    schema['onboarded_on']={'id':'onboarded','type':'rich_text'}
    source={'id':SOURCE,'parent':{'database_id':INTAKE_DATABASE_ID},'last_edited_time':'source-fixed','properties':{
        'Raw Property Data':{'id':'raw','type':'rich_text',**serialize_notion('original raw','rich_text')},
        'Photos':{'id':'photos','type':'files','files':[]},
        'Listing ID':{'id':'source-id','type':'rich_text',**serialize_notion('','rich_text')},
        'Processed Property':{'id':'relation','type':'relation','relation':[],'has_more':False}}}
    class Client:
        def __init__(self):self.source=source;self.page=None;self.duplicates=False;self.after_get=lambda:None
        def get_page(self,page):
            result=deepcopy(self.source if page==SOURCE else self.page)
            self.after_get();return result
        def request(self,method,path,payload=None):
            assert method=='POST' and path==f'databases/{PARENT}/query'
            rows=[] if self.page is None else [deepcopy(self.page)]
            if self.duplicates and rows:rows.append({**rows[0],'id':SOURCE})
            return {'results':rows,'has_more':False}
    client=Client()
    class Response:
        ok=True;status_code=201;headers={'x-request-id':'create-response-1'}
        def __init__(self,body):self.body=body
        def json(self):return deepcopy(self.body)
    class Session:
        count=0;timeout=False;bad_request=False;bad_page=False;saved503=False
        after_post=lambda self:None
        def request(self,method,url,**kw):
            assert method=='POST' and url=='https://api.notion.com/v1/pages'
            self.count+=1
            properties={}
            for name,definition in schema.items():
                kind=definition['type']
                value=kw['json']['properties'].get(name,{'formula':{'type':'number','number':0}})
                properties[name]={'id':definition['id'],'type':kind,**deepcopy(value)}
            client.page={'id':PAGE,'parent':{'database_id':PARENT},'archived':False,'last_edited_time':'created','properties':properties}
            response=Response(deepcopy(client.page));self.after_post()
            if self.timeout:raise TimeoutError('create response lost')
            if self.bad_request:response.headers={}
            if self.bad_page:response.body.pop('id')
            if self.saved503:
                response.ok=False;response.status_code=503
                response.body={'code':'service_unavailable','additional_data':{'retry_guidance':['Read the object again to confirm the saved change.','Do not repeat the write.']}}
            return response
    source_schema={k:{'id':v['id'],'type':v['type']}for k,v in source['properties'].items()}
    source_schema['Processed Property']['relation']={'database_id':PARENT}
    session=Session();http=V5HttpNotionClient(token='synthetic',version='2022-06-28',session=session)
    counts={'media':0,'pipeline':0}
    def photos(*a,**kw):counts['media']+=1;return [],[]
    def extract(*a,**kw):
        counts['pipeline']+=1
        return {**deepcopy(processed),'listing_id':kw['row']['listing_id']},[]
    monkeypatch.setattr(notion_intake,'_upload_photos',photos)
    monkeypatch.setattr(notion_intake.pipeline,'process_closed_session',extract)
    monkeypatch.setattr(notion_intake,'build_whatsapp_post',lambda *a,**kw:'')
    class PipelineClient:_listing_schema={'locality':{'type':'select','select':{'options':[]}}}
    policy={'visibility':'isolated_fixture_only','availability':'Available','pipeline':'Processing','live_on':[],'title':'','ownership':'unknown_until_proven'}
    args={'source_page_id':SOURCE,'payload_hash':source_payload_hash(source),'repository':CreateRepository(db.request),
        'client':client,'http':http,'schema_loader':lambda:deepcopy(schema),'sealed_schema_hash':content_hash(schema),
        'source_schema_loader':lambda:deepcopy(source_schema),'sealed_source_hash':content_hash(source_schema),
        'policy':policy,'sealed_policy_hash':content_hash(policy),'onboarded_at':'2026-11-15T20:00:00+00:00',
        'pipeline_client':PipelineClient(),'cloudinary':object(),'maps_client':object(),'ola_client':object()}
    return args,client,session,counts


def test_one_post_full_response_readback_atomic_bootstrap_unknown_ownership(db,monkeypatch):
    args,c,s,counts=setup(db,monkeypatch);out=create_fixture(**args)
    assert out['phase']=='bootstrapped' and out['fixture_only'] and not out['source_completion_allowed']
    x=db.request('__inspect');r=x['creations'][0]
    assert re.fullmatch(r'EF-\d{4}-[0123456789ABCDEFGHJKMNPQRSTVWXYZ]{4}',r['listing_id'])
    assert r['page_id']==PAGE and s.count==1 and counts=={'media':1,'pipeline':1}
    assert x['state']['revision']==1 and x['state']['last_acknowledged_values']['SL number']==''
    assert all(v['origin']=='legacy_unknown'for v in x['state']['field_provenance'].values())
    assert str(x['mirror']['monthly_rent'])=='25000'
    assert x['mirror']['listing_state']=='Available' and x['mirror']['pipeline_status']=='Processing' # fixture ONLY, not visibility safety
    assert len(x['membership'])==1 and x['jobs'][0]['ordered_page_ids']==[PAGE]
    assert c.source['properties']['Processed Property']['relation']==[]
    assert create_fixture(**args)['phase']=='bootstrapped' and s.count==1 and counts['pipeline']==1


@pytest.mark.parametrize('lost',['transport','receipt','request_id','page_id','503'])
def test_any_unknown_create_never_adopts_query_match_or_reposts(db,monkeypatch,lost):
    args,c,s,counts=setup(db,monkeypatch)
    if lost=='transport':s.timeout=True
    elif lost=='request_id':s.bad_request=True
    elif lost=='page_id':s.bad_page=True
    elif lost=='503':s.saved503=True
    else:
        orig=args['repository'].call
        def fail(op,*a,**kw):
            if op=='receipt':raise TimeoutError('receipt save lost')
            return orig(op,*a,**kw)
        args['repository'].call=fail
    with pytest.raises((RuntimeError,TimeoutError)):create_fixture(**args)
    db.request('__expire')
    out=create_fixture(**args)
    assert out['held'] and out['unknown_create'] and s.count==1 and counts['media']==1
    x=db.request('__inspect');assert x.get('state') is None and x.get('mirror') is None and not x['membership']


def test_terminal_receipt_restart_bootstrap_response_loss_is_idempotent(db,monkeypatch):
    args,c,s,counts=setup(db,monkeypatch);orig=args['repository'].call
    def fail(op,*a,**kw):
        value=orig(op,*a,**kw)
        if op=='bootstrap':raise TimeoutError('bootstrap response lost')
        return value
    args['repository'].call=fail
    with pytest.raises(TimeoutError):create_fixture(**args)
    args['repository'].call=orig
    assert create_fixture(**args)['phase']=='bootstrapped' and s.count==1 and counts['media']==1
    x=db.request('__inspect');assert len(x['membership'])==1 and len(x['jobs'])==1 and x['state']['revision']==1


@pytest.mark.parametrize('edit',['owner','source','duplicate','parent'])
def test_postreceipt_edits_or_duplicate_hold_before_bootstrap(db,monkeypatch,edit):
    args,c,s,counts=setup(db,monkeypatch)
    def change():
        if edit=='owner':c.page['properties']['monthly_rent']['number']=99999
        elif edit=='source':c.source['properties']['Raw Property Data']['rich_text'][0]['text']['content']='new raw'
        elif edit=='duplicate':c.duplicates=True
        else:c.page['parent']={'database_id':SOURCE}
    s.after_post=change
    with pytest.raises(IntakeDestinationBlocked):create_fixture(**args)
    x=db.request('__inspect');assert s.count==1 and x.get('state') is None and x.get('mirror') is None and not x['membership']
    assert x['creations'][0]['phase']=='receipted'


@pytest.mark.parametrize('invalid',['policy','source_relation','source_payload','schema'])
def test_preflight_refuses_before_media_or_create(db,monkeypatch,invalid):
    args,c,s,counts=setup(db,monkeypatch)
    if invalid=='policy':args['policy']=None
    elif invalid=='source_relation':c.source['properties']['Processed Property']['relation']=[{'id':PAGE}]
    elif invalid=='source_payload':c.source['properties']['Raw Property Data']['rich_text'][0]['text']['content']='changed'
    else:args['schema_loader']=lambda:{}
    with pytest.raises(IntakeDestinationBlocked):create_fixture(**args)
    assert s.count==0 and counts['media']==0 and db.request('__inspect')['creations']==[]


@pytest.mark.parametrize('boundary',['claim','pipeline_output','receipt'])
def test_saved_response_loss_resumes_exact_allocated_id_output_and_receipt(db,monkeypatch,boundary):
    args,c,s,counts=setup(db,monkeypatch);orig=args['repository'].call;once=[False]
    def lost(op,*a,**kw):
        value=orig(op,*a,**kw)
        if op==boundary and not once[0]:once[0]=True;raise TimeoutError('saved phase response lost')
        return value
    args['repository'].call=lost
    with pytest.raises(TimeoutError):create_fixture(**args)
    before=db.request('__inspect')['creations'][0];db.request('__expire')
    args['repository'].call=orig
    assert create_fixture(**args)['phase']=='bootstrapped'
    after=db.request('__inspect')['creations'][0]
    assert after['listing_id']==before['listing_id'] and s.count==1 and counts['media']==1


def test_unsaved_pipeline_output_holds_and_never_repeats_media(db,monkeypatch):
    args,c,s,counts=setup(db,monkeypatch);orig=args['repository'].call
    def lost(op,*a,**kw):
        if op=='pipeline_output':raise TimeoutError('output not saved')
        return orig(op,*a,**kw)
    args['repository'].call=lost
    with pytest.raises(TimeoutError):create_fixture(**args)
    args['repository'].call=orig;db.request('__expire')
    assert create_fixture(**args)['uncaptured_pipeline'] and counts['media']==1 and s.count==0


def test_bootstrap_transaction_failure_rolls_back_row_mirror_provenance_and_membership(db,monkeypatch):
    args,c,s,counts=setup(db,monkeypatch);db.request('__fail_membership',enabled=True)
    with pytest.raises(RuntimeError):create_fixture(**args)
    x=db.request('__inspect')
    assert x.get('state') is None and x.get('mirror') is None and not x['provenance'] and not x['membership'] and not x['jobs']
    assert x['creations'][0]['phase']=='receipted' and s.count==1
    db.request('__fail_membership',enabled=False)
    assert create_fixture(**args)['phase']=='bootstrapped' and s.count==1 and counts['pipeline']==1


def test_legacy_id_change_after_reservation_never_changes_immutable_create_identity(db,monkeypatch):
    args,c,s,counts=setup(db,monkeypatch);orig=args['repository'].call
    def stop(op,*a,**kw):
        value=orig(op,*a,**kw)
        if op=='claim':raise TimeoutError('allocated claim response lost')
        return value
    args['repository'].call=stop
    with pytest.raises(TimeoutError):create_fixture(**args)
    old=db.request('__inspect')['creations'][0]['listing_id'];db.request('__expire')
    db.request('__legacy_change',source_page_id=SOURCE,listing_id='EF-2611-ZZZZ')
    args['repository'].call=orig
    with pytest.raises(RuntimeError):create_fixture(**args)
    assert db.request('__inspect')['creations'][0]['listing_id']==old and s.count==0 and counts['media']==0


@pytest.mark.parametrize('boundary',['begin','dispatch'])
def test_begun_unknown_intent_never_retries_even_if_process_stopped_before_post(db,monkeypatch,boundary):
    args,c,s,counts=setup(db,monkeypatch);orig=args['repository'].call
    def stop(op,*a,**kw):
        value=orig(op,*a,**kw)
        if op==boundary:raise TimeoutError('unknown process boundary')
        return value
    args['repository'].call=stop
    with pytest.raises(TimeoutError):create_fixture(**args)
    args['repository'].call=orig;db.request('__expire')
    assert create_fixture(**args)['unknown_create'] and s.count==0 and counts['media']==1


def test_wrong_receipt_dispatch_or_nonce_refuses_even_after_real_response(db,monkeypatch):
    args,c,s,counts=setup(db,monkeypatch);orig=args['repository'].call
    def wrong(op,*a,**kw):
        if op=='receipt':kw['value']['dispatch']['nonce']=SOURCE
        return orig(op,*a,**kw)
    args['repository'].call=wrong
    with pytest.raises(RuntimeError):create_fixture(**args)
    x=db.request('__inspect');assert x['creations'][0]['phase']=='dispatching' and x.get('state') is None and s.count==1


def test_lease_expiry_after_post_cannot_receipt_or_bootstrap(db,monkeypatch):
    args,c,s,counts=setup(db,monkeypatch);s.after_post=lambda:db.request('__expire')
    with pytest.raises(RuntimeError):create_fixture(**args)
    assert create_fixture(**args)['unknown_create'] and s.count==1 and db.request('__inspect').get('state') is None


def test_existing_legacy_claim_is_not_adopted_as_safe_new_create(db,monkeypatch):
    args,c,s,counts=setup(db,monkeypatch)
    db.request('__legacy_binding',source_page_id=SOURCE,listing_id='EF-2611-ABCD',page_id='',payload_hash=args['payload_hash'])
    with pytest.raises(RuntimeError):create_fixture(**args)
    assert not db.request('__inspect')['creations'] and s.count==0 and counts['media']==0


def test_reserved_creation_fences_legacy_claim_and_allocator_and_concurrent_controller(db,monkeypatch):
    args,c,s,counts=setup(db,monkeypatch);orig=args['repository'].call;seen=[]
    def call(op,*a,**kw):
        value=orig(op,*a,**kw)
        if op=='pipeline_begin':
            seen.append(db.request('claim',page_id=SOURCE,payload_hash=args['payload_hash']))
            assert create_fixture(**args)['held']
            with pytest.raises(RuntimeError):db.request('allocate_listing_id',page_id=SOURCE)
        return value
    args['repository'].call=call
    assert create_fixture(**args)['phase']=='bootstrapped'
    assert seen[0]['status']=='in_progress' and seen[0]['v5_create_held'] and s.count==1


def test_changed_source_after_output_freeze_refuses_post(db,monkeypatch):
    args,c,s,counts=setup(db,monkeypatch);orig=args['repository'].call
    def changed(op,*a,**kw):
        value=orig(op,*a,**kw)
        if op=='pipeline_output':c.source['properties']['Raw Property Data']['rich_text'][0]['text']['content']='changed before POST'
        return value
    args['repository'].call=changed
    with pytest.raises(IntakeDestinationBlocked):create_fixture(**args)
    assert s.count==0 and counts['media']==1 and db.request('__inspect')['creations'][0]['phase']=='planned'


@pytest.mark.parametrize('bad',['provenance','mirror','readback','source_schema'])
def test_bootstrap_forged_arguments_refuse_atomic_state(db,monkeypatch,bad):
    args,c,s,counts=setup(db,monkeypatch);orig=args['repository'].call
    def tamper(op,*a,**kw):
        if op=='bootstrap':
            if bad=='provenance':kw['value']['provenance']['monthly_rent']['origin']='derived'
            elif bad=='mirror':kw['value']['mirror']['monthly_rent']=99999
            elif bad=='readback':kw['value']['readback']['values']['monthly_rent']=99999
            else:kw['value']['schema']['source']['Listing ID']['id']='forged'
        return orig(op,*a,**kw)
    args['repository'].call=tamper
    with pytest.raises(RuntimeError):create_fixture(**args)
    x=db.request('__inspect');assert x.get('state') is None and x.get('mirror') is None and not x['membership'] and not x['provenance']
    assert x['creations'][0]['phase']=='receipted' and s.count==1


def test_readonly_owner_field_change_blocks_full_response_get_comparison(db,monkeypatch):
    args,c,s,counts=setup(db,monkeypatch)
    s.after_post=lambda:c.page['properties']['_SL numeric sort'].update({'formula':{'type':'number','number':999}})
    with pytest.raises(IntakeDestinationBlocked,match='changed since terminal'):create_fixture(**args)
    assert s.count==1 and db.request('__inspect').get('state') is None


def test_another_legacy_source_cannot_receive_reserved_id(db,monkeypatch):
    args,c,s,counts=setup(db,monkeypatch);create_fixture(**args)
    reserved=db.request('__inspect')['creations'][0]['listing_id']
    db.request('__legacy_binding',source_page_id=PAGE,listing_id=reserved,page_id='',payload_hash='b'*64)
    with pytest.raises(RuntimeError):db.request('allocate_listing_id',page_id=PAGE)
    assert len(db.request('__inspect')['creations'])==1 and s.count==1
