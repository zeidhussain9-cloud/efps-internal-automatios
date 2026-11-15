from copy import deepcopy
import pytest
from test_inventory_v5_full_ports import DB,Client,PAGE
from test_inventory_v5_intake import fixture
from src.inventory_v5_adapter import serialize_notion
from src.inventory_v5_intake import destination_candidate,IntakeDestinationBlocked,PARENT
from src.inventory_v5_intake_executor import save_existing_destination,SubmissionRepository
from src.inventory_v5_repository import V5Repository
from src.inventory_v5_notion import V5NotionPort
from src.inventory_v5_http import V5HttpNotionClient
from src.inventory_v5 import content_hash
SOURCE='12345678-1234-4234-8234-123456789013'

@pytest.fixture
def db():
    x=DB();yield x;x.close()


def setup(db):
    processed,schema=fixture();candidate=destination_candidate(processed,schema=schema,sealed_schema_hash=content_hash(schema))
    row={**candidate,'SL number':'1','Availability':'Available','Pipeline Status':'Ready to Post','Live On':[],
         'onboarded_on':'Sunday, November 15, 2026 at 02:41:00 pm'}
    schema['onboarded_on']={'id':'onboarded','type':'rich_text'}
    client=Client({k:v for k,v in row.items()if k!='Live On'})
    client.schema=schema
    client.row={k:{'type':schema[k]['type'],**serialize_notion(v,schema[k]['type'])}for k,v in row.items()}
    orig=client.get_page;client.get_page=lambda page:{**orig(page),'parent':{'database_id':PARENT}}
    class Response:
        ok=True;status_code=200;headers={}
        def __init__(self,body):self.body=body
        def json(self):return self.body
    class Session:
        count=0;timeout=False;after_patch=lambda self:None
        def request(self,method,url,**kw):
            if method=='GET':return Response(client.get_page(PAGE))
            self.count+=1;client.update_page(PAGE,kw['json']['properties']);self.after_patch()
            if self.timeout:raise TimeoutError('unknown destination flight')
            return Response({})
    session=Session();http=V5HttpNotionClient(token='synthetic',version='2022-06-28',session=session)
    notion=V5NotionPort(http,schema,expected_parent=PARENT)
    ack=notion.snapshot(PAGE)
    db.request('__seed',page_id=PAGE,row=ack,provenance={'monthly_rent':{'origin':'derived','last_generated_value':25000,'derivation_version':5}})
    def mirror(page,values,*,deleted,lease,revision):
        value={**values,'inventory_contract_version':5,'onboarded_at':'2026-11-15T09:11:00Z'}
        return db.request('sync_inventory',page_id=page,listing_id=value['listing_id'],row=value,deleted=deleted,lease=lease,revision=revision,source_hash=content_hash(value))
    workers=V5Repository(request=db.request,identity=lambda page:processed['listing_id'],mirror=mirror)
    args=dict(source_page_id=SOURCE,payload_hash='a'*64,page_id=PAGE,processed={**processed,'monthly_rent':26000},workers=workers,
        submissions=SubmissionRepository(db.request),notion=notion,schema_loader=lambda:deepcopy(schema),sealed_schema_hash=content_hash(schema),
        verify_binding=lambda source,listing,page:{'source_page_id':source,'listing_id':listing,'page_id':page,'active':True,'unique':True})
    return args,client,session


def test_existing_destination_actual_write_mirror_provenance_source_pending(db):
    args,c,s=setup(db);out=save_existing_destination(**args)
    assert out['status']=='awaiting_source_ack' and not out['source_completion_allowed'] and s.count==1
    x=db.request('__inspect')
    assert x['state']['last_acknowledged_values']['monthly_rent']==26000
    assert x['state']['field_provenance']['monthly_rent']['last_generated_value']==26000
    assert x['mirror']['source_record']['monthly_rent']==26000
    assert x['submissions'][0]['phase']=='awaiting_source_ack'
    assert save_existing_destination(**args)['status']=='awaiting_source_ack' and s.count==1


def test_owner_edit_after_prepare_does_not_advance_or_replay(db):
    args,c,s=setup(db)
    s.after_patch=lambda:c.update_page(PAGE,{'monthly_rent':serialize_notion(27000,'number')})
    with pytest.raises(IntakeDestinationBlocked,match='readback'):save_existing_destination(**args)
    x=db.request('__inspect')
    assert x['state']['pending_kind']=='intake' and x['state']['last_acknowledged_values']['monthly_rent']==25000
    assert x['state']['field_provenance']['monthly_rent']['last_generated_value']==25000
    with pytest.raises(IntakeDestinationBlocked,match='owner values'):save_existing_destination(**args)
    assert s.count==1


def test_unknown_flight_keeps_barrier_and_blocks_genericworker(db):
    args,c,s=setup(db);s.timeout=True
    with pytest.raises(TimeoutError):save_existing_destination(**args)
    x=db.request('__inspect');assert x['state']['active_effect']['dispatch']['effect_id']
    db.request('__expire')
    assert args['workers'].claim(PAGE) is None
    assert save_existing_destination(**args)['status']=='busy' and s.count==1


def test_crash_after_ack_before_sourceledger_retries_without_second_patch(db):
    args,c,s=setup(db);sub=args['submissions'];orig=sub.call
    def call(op,*a,**kw):
        if op=='destination_ack':raise TimeoutError('source ledger response lost')
        return orig(op,*a,**kw)
    sub.call=call
    with pytest.raises(TimeoutError):save_existing_destination(**args)
    sub.call=orig
    assert save_existing_destination(**args)['status']=='awaiting_source_ack' and s.count==1


def test_conflicting_payload_or_page_binding_refused_not_replayed(db):
    args,c,s=setup(db);save_existing_destination(**args)
    with pytest.raises(RuntimeError):save_existing_destination(**{**args,'payload_hash':'b'*64})
    args['verify_binding']=lambda *a:{'unique':False}
    with pytest.raises(IntakeDestinationBlocked,match='binding'):save_existing_destination(**args)
    assert s.count==1


def test_changed_schema_refuses_before_destination_write(db):
    args,c,s=setup(db);args['processed']['security_deposit']=100000
    args['notion'].schema['security_deposit']={'id':'deposit','type':'number'}
    c.row['security_deposit']={'type':'number','number':None}
    # Changing schema/baseline after the reviewed seal is itself refused.
    with pytest.raises(IntakeDestinationBlocked,match='seal'):save_existing_destination(**args)
    assert s.count==0


def test_crash_after_plan_before_row_prepare_resumes_one_patch(db):
    args,c,s=setup(db);workers=args['workers'];orig=workers._call
    def call(op,*a,**kw):
        if op=='prepare_intake':raise TimeoutError('crash before row prepare')
        return orig(op,*a,**kw)
    workers._call=call
    with pytest.raises(TimeoutError):save_existing_destination(**args)
    assert db.request('__inspect')['submissions'][0]['phase']=='planned'
    workers._call=orig
    assert save_existing_destination(**args)['status']=='awaiting_source_ack' and s.count==1


def test_crash_after_prepare_before_effect_resumes_exact_pending_intake(db):
    args,c,s=setup(db);workers=args['workers'];orig=workers.effect
    workers.effect=lambda *a:(_ for _ in ()).throw(TimeoutError('crash before effect'))
    with pytest.raises(TimeoutError):save_existing_destination(**args)
    assert workers.claim(PAGE) is None
    x=db.request('__inspect')['state']
    assert x['field_provenance']['monthly_rent']['last_generated_value']==25000
    workers.effect=orig
    assert save_existing_destination(**args)['status']=='awaiting_source_ack' and s.count==1


def test_mirror_failure_does_not_ack_source_or_advance_provenance(db):
    args,c,s=setup(db);workers=args['workers'];orig=workers.mirror_port
    workers.mirror_port=lambda *a,**kw:(_ for _ in ()).throw(TimeoutError('mirror request lost'))
    with pytest.raises(TimeoutError):save_existing_destination(**args)
    x=db.request('__inspect')
    assert x['submissions'][0]['phase']=='planned' and x['state']['pending_kind']=='intake'
    assert x['state']['field_provenance']['monthly_rent']['last_generated_value']==25000
    workers.mirror_port=orig
    assert save_existing_destination(**args)['status']=='awaiting_source_ack' and s.count==1


def test_unchanged_input_still_requires_mirror_and_durable_destination_ack(db):
    args,c,s=setup(db);args['processed']['monthly_rent']=25000
    assert save_existing_destination(**args)['status']=='awaiting_source_ack'
    x=db.request('__inspect')
    assert s.count==0 and x['state']['revision']==2
    assert x['mirror']['source_record']['monthly_rent']==25000


def test_legacy_owner_conflict_writes_only_review_and_preserves_value(db):
    args,c,s=setup(db);args['processed']['catalog_title']='new extracted title'
    out=save_existing_destination(**args)
    assert out['conflicts']==['catalog_title'] and not out['source_completion_allowed']
    x=db.request('__inspect')
    assert x['state']['last_acknowledged_values']['catalog_title']=='catalog name'
    assert x['state']['last_acknowledged_values']['Pipeline Status']=='Needs Review'
    assert x['submissions'][0]['phase']=='awaiting_source_ack'
    assert set(c.patches[-1])=={'monthly_rent','Pipeline Status'}


def test_expired_submission_lease_cannot_ack_or_overwrite_plan(db):
    args,c,s=setup(db);sub=args['submissions']
    record=sub.call('claim',SOURCE,page_id=PAGE,payload_hash='a'*64,listing_id='EF-2611-ABCD',candidate={})
    lease=record['lease_token'];db.request('__expire')
    with pytest.raises(RuntimeError):sub.call('plan',SOURCE,lease,plan={})
    with pytest.raises(RuntimeError):sub.call('destination_ack',SOURCE,lease)


def test_ledger_cannot_claim_destination_ack_before_row_and_mirror(db):
    args,c,s=setup(db);sub=args['submissions']
    record=sub.call('claim',SOURCE,page_id=PAGE,payload_hash='a'*64,listing_id='EF-2611-ABCD',candidate={})
    lease=record['lease_token'];before=args['notion'].snapshot(PAGE)
    sub.call('plan',SOURCE,lease,plan={'before':before,'patch':{},'revision':1})
    with pytest.raises(RuntimeError):sub.call('destination_ack',SOURCE,lease)
    with pytest.raises(RuntimeError):sub.call('finish',SOURCE,lease)
    assert db.request('__inspect')['submissions'][0]['phase']=='planned'
