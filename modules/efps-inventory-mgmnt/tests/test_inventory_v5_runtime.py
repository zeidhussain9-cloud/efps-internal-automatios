"""No external account requests: runtime routing and old-queue isolation."""
from copy import deepcopy
import os
import pytest
from src import notion_intake as intake
from src.inventory_v5 import content_hash
from src.inventory_v5_runtime import process_existing_housing, RuntimeBlocked
from test_inventory_v5_full_ports import DB, Client, PAGE
from src.inventory_v5_notion import V5NotionPort
from src.inventory_v5_adapter import serialize_notion


@pytest.fixture
def db():
    value = DB()
    yield value
    value.close()


class HttpSession:
    def __init__(self, client): self.client=client; self.calls=[]
    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs.get('json')))
        page=url.rsplit('/',1)[1]
        if method=='GET': result=self.client.get_page(page)
        else:
            self.client.update_page(page, kwargs['json']['properties']); result={}
        class Response:
            ok=True; status_code=200; headers={}
            def json(self):return result
        return Response()


class Store:
    def __init__(self, db):self.db=db; self.calls=[]; self.deleted=None; self.found=True
    def find_inventory(self,page):return {'found':self.found,'listing_id':'EF-2611-ABCD','deleted_at':self.deleted}
    def _request(self,operation,**kwargs):
        self.calls.append((operation,kwargs));return self.db.request(operation,**kwargs)


def runtime_fixture(db):
    row={'listing_id':'EF-2611-ABCD','Pipeline Status':'Ready to Post',
         'Availability':'Available','Live On':[], 'SL number':'1',
         'onboarded_on':'Sunday, November 15, 2026 at 02:41:00 pm',
         'built_up_area':1200,'carpet_area':1110,'whatsapp_post':'caption'}
    client=Client({k:v for k,v in row.items()if k!='Live On'})
    for name,kind,options in [('SL number','title',[]),('Availability','select',['Available','On Hold','Rented Out']),('Live On','multi_select',[])]:
        client.schema[name]={'id':name,'type':kind,kind:{'options':[{'name':x}for x in options]}if kind in ['select','multi_select']else{}}
        client.row[name]={'type':kind,**serialize_notion(row[name],kind)}
    client.schema['_SL numeric sort']={'id':'sort','type':'formula','formula':{'expression':'toNumber(prop("SL number"))'}}
    original_get=client.get_page
    client.get_page=lambda page:{**original_get(page),'parent':{'database_id':intake.LISTINGS_DATABASE_ID}}
    client.token='test-token';client.session=HttpSession(client)
    ack=V5NotionPort(client,client.schema).snapshot(PAGE)
    db.request('__seed',page_id=PAGE,row=ack,provenance={'carpet_area':{'origin':'derived','last_generated_value':'1110'},'whatsapp_post':{'origin':'derived','last_generated_value':'caption'}})
    store=Store(db)
    return client,store


def run(client,store,seal=None):
    return process_existing_housing(PAGE,client=client,store=store,schema=client.schema,
        sealed_schema_hash=seal if seal is not None else content_hash(client.schema),
        render_caption=lambda row:'caption',route_bhk=lambda bhk:('',''))


def test_runtime_real_ports_recompute_and_old_payload_redelivery_refetches_latest(db):
    client,store=runtime_fixture(db)
    client.update_page(PAGE,{'built_up_area':serialize_notion(1300,'number')})
    out=run(client,store)
    assert out['status']=='recalculated'
    assert client.row['carpet_area']['number']==1210
    assert db.request('__inspect')['mirror']['source_record']['carpet_area']==1210
    patch_count=len([c for c in client.session.calls if c[0]=='PATCH'])
    # An old queue delivery passes only page identity. Current Notion is fetched,
    # not a stale event snapshot; legacy dedup/mirror ports are never called.
    again=run(client,store)
    assert again['status']=='self_write_acknowledged'
    assert len([c for c in client.session.calls if c[0]=='PATCH'])==patch_count
    assert all(op in ['inventory_v5_worker','sync_inventory']for op,_ in store.calls)
    mirror=db.request('__inspect')['mirror']
    assert mirror['inventory_contract_version']==5
    assert mirror['onboarded_at'].startswith('2026-11-15T09:11:00')


def test_runtime_missing_or_changed_schema_seal_has_no_remote_effect(db):
    client,store=runtime_fixture(db)
    for seal in ['', '0'*64]:
        with pytest.raises(RuntimeBlocked):run(client,store,seal)
    assert not store.calls and not client.session.calls


def test_runtime_new_deleted_or_archived_membership_fails_without_legacy_write(db):
    client,store=runtime_fixture(db)
    store.found=False
    with pytest.raises(RuntimeBlocked):run(client,store)
    store.found=True;store.deleted='2026-11-15T00:00:00Z'
    with pytest.raises(RuntimeBlocked):run(client,store)
    store.deleted=None
    old=client.get_page
    client.get_page=lambda page:{**old(page),'archived':True}
    with pytest.raises(RuntimeBlocked):run(client,store)
    assert not store.calls
    assert not any(c[0]=='PATCH'for c in client.session.calls)


def test_runtime_refuses_unseeded_identity_before_notion_patch(db):
    client,store=runtime_fixture(db)
    # Different valid mirror identity cannot bootstrap provenance or take the row.
    store.find_inventory=lambda page:{'found':True,'listing_id':'EF-2611-ZZZZ'}
    with pytest.raises(Exception):run(client,store)
    assert not any(c[0]=='PATCH'for c in client.session.calls)


def test_listing_route_flag_defaults_to_exact_legacy_path(monkeypatch):
    monkeypatch.delenv('EFPS_INVENTORY_V5_ENABLED',raising=False)
    class Legacy:
        def __init__(self):self.calls=[]
        def claim(self,*a):self.calls.append('claim');return 'in_progress',{'listing_id':'EF-2611-ABCD'}
    store=Legacy();page={'id':PAGE,'properties':{}}
    assert intake.process_listing_page(page,notion=object(),store=store)=={'status':'processing','listing_id':'EF-2611-ABCD'}
    assert store.calls==['claim']
    monkeypatch.setenv('EFPS_INVENTORY_V5_ENABLED','TRUE')
    intake.process_listing_page(page,notion=object(),store=store)
    assert store.calls==['claim','claim']


def test_enabled_listing_route_never_touches_legacy_claim_or_falls_back(monkeypatch):
    monkeypatch.setenv('EFPS_INVENTORY_V5_ENABLED','true')
    seen=[]
    def blocked(*a,**k):seen.append(a);raise RuntimeBlocked('test gate')
    monkeypatch.setattr(intake,'_process_existing_housing_v5',blocked)
    with pytest.raises(RuntimeBlocked):intake.process_listing_page({'id':PAGE},notion=object(),store=object())
    assert len(seen)==1
    with pytest.raises(intake.IntakeError):intake.process_listing_page({'id':PAGE},notion=object(),store=object(),force_deleted=True)


def test_enabled_archive_and_delete_do_not_take_legacy_shortcuts(monkeypatch):
    monkeypatch.setenv('EFPS_INVENTORY_V5_ENABLED','true')
    class Notion:
        def get_page(self,page):return {'id':page,'archived':True,'parent':{'database_id':intake.LISTINGS_DATABASE_ID}}
    class Store:
        def find_inventory(self,page):return {'found':True}
    monkeypatch.setattr(intake,'_process_existing_housing_v5',lambda *a,**k:{'status':'test_existing'})
    assert intake.process_page(PAGE,notion=Notion(),store=Store())['status']=='test_existing'
    with pytest.raises(intake.IntakeError):intake.process_page(PAGE,notion=Notion(),store=Store(),event_type='page.deleted')


def test_enabled_raw_intake_archive_still_uses_original_flow(monkeypatch):
    monkeypatch.setenv('EFPS_INVENTORY_V5_ENABLED','true')
    class Notion:
        def get_page(self,page):return {'id':page,'archived':True,'parent':{'database_id':intake.INTAKE_DATABASE_ID}}
    class Store:
        def finish(self,*a,**k):pass
        def find_inventory(self,page):return {'found':False}
    assert intake.process_page(PAGE,notion=Notion(),store=Store())['reason']=='source_page_deleted'


def test_enabled_reconciler_is_blocked_before_legacy_or_external_effect(monkeypatch):
    monkeypatch.setenv('EFPS_INVENTORY_V5_ENABLED','true')
    with pytest.raises(intake.IntakeError):intake._enqueue_listing_backfill('not-used')


@pytest.mark.parametrize('status',['busy','retry','needs_recovery','unrecognized'])
def test_old_queue_never_acknowledges_pending_v5_outcomes(monkeypatch,status):
    monkeypatch.setattr(intake,'process_page',lambda *a,**k:{'status':status,'inventory_contract_version':5})
    class Context:aws_request_id='test-request'
    with pytest.raises(intake.IntakeError):intake.lambda_handler({'_efps_notion_worker':True,'page_id':PAGE},Context())


def test_v5_review_status_maps_to_existing_event_ledger_without_legacy_change(monkeypatch):
    writes=[]
    class EventStore:
        def update_webhook_event(self,row,status,**kw):writes.append(status);return {}
    monkeypatch.setattr(intake,'SupabaseIntakeStore',EventStore)
    monkeypatch.setattr(intake,'process_page',lambda *a,**k:{'status':'needs_review','inventory_contract_version':5})
    class Context:aws_request_id='test-request'
    intake.lambda_handler({'_efps_notion_worker':True,'page_id':PAGE,'event_row_id':'notion-webhook:test'},Context())
    assert writes==['processing','needs_review']


@pytest.mark.parametrize('archived',[False,True])
@pytest.mark.parametrize('parent',[intake.INTAKE_DATABASE_ID,'123456781234423482341234567890ab'])
def test_known_housing_moved_to_other_parent_never_enters_legacy_or_raw_intake(monkeypatch,archived,parent):
    monkeypatch.setenv('EFPS_INVENTORY_V5_ENABLED','true')
    seen=[]
    class Notion:
        def get_page(self,page):return {'id':page,'archived':archived,'parent':{'database_id':parent},'properties':{}}
        def update_page(self,*a,**k):seen.append('notion_write')
    class Store:
        def find_inventory(self,page):return {'found':True,'listing_id':'EF-2611-ABCD'}
        def claim(self,*a,**k):seen.append('legacy_claim');raise AssertionError('legacy claim')
        def finish(self,*a,**k):seen.append('legacy_finish')
    class Media:
        def __getattr__(self,name):raise AssertionError('media port used')
    with pytest.raises(intake.IntakeError,match='moved outside Housing'):
        intake.process_page(PAGE,event_type='page.moved',notion=Notion(),store=Store(),cloudinary=Media())
    assert seen==[]


@pytest.mark.parametrize('parent',[intake.INTAKE_DATABASE_ID,'','123456781234423482341234567890ab'])
def test_direct_runtime_rechecks_current_parent_before_any_patch_or_mirror(db,parent):
    client,store=runtime_fixture(db)
    original_get=client.get_page
    client.get_page=lambda page:{**original_get(page),'parent':{'database_id':parent}}
    with pytest.raises(ValueError,match='expected Housing parent'):run(client,store)
    assert not store.calls
    assert not any(c[0]=='PATCH'for c in client.session.calls)


def test_runtime_move_during_prewrite_recheck_refuses_patch_and_mirror(db):
    client,store=runtime_fixture(db)
    client.update_page(PAGE,{'built_up_area':serialize_notion(1300,'number')})
    original_get=client.get_page;reads=[]
    def moved(page):
        reads.append(page)
        result=original_get(page)
        # Initial runtime boundary read and worker read are Housing. A move
        # before worker prewrite refetch is visible and must stop the write.
        if len(reads)>=3:result['parent']={'database_id':intake.INTAKE_DATABASE_ID}
        return result
    client.get_page=moved
    with pytest.raises(ValueError,match='expected Housing parent'):run(client,store)
    assert not any(c[0]=='PATCH'for c in client.session.calls)
    assert not any(op=='sync_inventory'for op,_ in store.calls)
