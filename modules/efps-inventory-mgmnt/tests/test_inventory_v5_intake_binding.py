from copy import deepcopy
import pytest
from test_inventory_v5_intake_executor import setup,SOURCE,db
from test_inventory_v5_full_ports import PAGE
from src.inventory_v5_intake import IntakeDestinationBlocked,PARENT
from src.inventory_v5_intake_binding import ExistingBindingResolver,prepare_source_ack,source_payload_hash,INTAKE_DATABASE_ID
from src.inventory_v5_intake_executor import save_existing_destination
from src.inventory_v5_adapter import serialize_notion


def port(db,save=True):
    args,c,s=setup(db)
    source={'id':SOURCE,'parent':{'database_id':INTAKE_DATABASE_ID},'last_edited_time':'fixed',
            'properties':{
            'Raw Property Data':{'type':'rich_text',**serialize_notion('original raw input','rich_text')},
            'Photos':{'type':'files','files':[]},
            'Listing ID':{'type':'rich_text',**serialize_notion('EF-2611-ABCD','rich_text')},
            'Processed Property':{'type':'relation','relation':[{'id':PAGE}],'has_more':False},
            'Intake Status':{'type':'status','status':{'name':'Processing'}}}}
    args['payload_hash']=source_payload_hash(source)
    if save:save_existing_destination(**args)
    class Client:
        def __init__(self):self.source=source;self.responses=None;self.reads=0
        def get_page(self,page):
            assert page==SOURCE
            return deepcopy(self.source)
        def request(self,method,path,payload=None):
            if method=='GET':
                return {'properties':{'Listing ID':{'type':'rich_text'},
                 'Processed Property':{'type':'relation','relation':{'database_id':PARENT}},
                 'Intake Status':{'type':'status','status':{'options':[{'name':'Processed'},{'name':'Needs Review'}]}}}}
            assert path==f'databases/{PARENT}/query'
            if self.responses is not None:
                result=self.responses[self.reads];self.reads+=1;return deepcopy(result)
            return {'results':[{'id':PAGE,'parent':{'database_id':PARENT},'properties':{'listing_id':{'type':'rich_text',**serialize_notion('EF-2611-ABCD','rich_text')}}}],'has_more':False}
    client=Client()
    resolver=ExistingBindingResolver(client=client,request=db.request,payload_hash=args['payload_hash'])
    return args,c,s,client,resolver


def test_actual_sql_binding_resolver_and_idempotent_source_ack_preparation_no_source_write(db):
    args,c,s,client,resolver=port(db)
    assert resolver(SOURCE,'EF-2611-ABCD',PAGE)['unique']
    kwargs=dict(source_page_id=SOURCE,payload_hash=args['payload_hash'],processed=args['processed'],submissions=args['submissions'],resolver=resolver)
    plan=prepare_source_ack(**kwargs)
    assert 'Intake Status' not in plan['properties'] and plan['source_status_unresolved']
    assert plan['properties']['Processed Property']=={'relation':[{'id':PAGE}]}
    assert not plan['source_completion_allowed'] and plan['destination_revision']==2
    assert prepare_source_ack(**kwargs)==plan
    saved=db.request('__inspect')['submissions'][0]
    assert saved['phase']=='awaiting_source_ack' and saved['source_ack_plan']==plan
    assert client.source['properties']['Intake Status']['status']['name']=='Processing'
    assert s.count==1  # only prior destination PATCH, zero source PATCHes


def test_duplicate_destination_on_later_page_and_broken_pagination_refuse(db):
    args,c,s,client,resolver=port(db)
    valid=client.request('POST',f'databases/{PARENT}/query')['results'][0]
    client.responses=[{'results':[valid],'has_more':True,'next_cursor':'next'},
                      {'results':[{**valid,'id':SOURCE}],'has_more':False}]
    with pytest.raises(IntakeDestinationBlocked,match='Multiple'):resolver(SOURCE,'EF-2611-ABCD',PAGE)
    client.reads=0;client.responses=[{'results':[],'has_more':True,'next_cursor':'repeat'},
                                   {'results':[],'has_more':True,'next_cursor':'repeat'}]
    with pytest.raises(IntakeDestinationBlocked,match='cyclic'):resolver(SOURCE,'EF-2611-ABCD',PAGE)


@pytest.mark.parametrize('change',['payload','relation','parent','archived','listing_id'])
def test_source_identity_relation_payload_and_parent_must_match(db,change):
    args,c,s,client,resolver=port(db)
    if change=='payload':client.source['properties']['Raw Property Data']={'type':'rich_text',**serialize_notion('new owner input','rich_text')}
    elif change=='relation':client.source['properties']['Processed Property']['relation']=[{'id':SOURCE}]
    elif change=='parent':client.source['parent']={'database_id':PARENT}
    elif change=='archived':client.source['archived']=True
    else:client.source['properties']['Listing ID']={'type':'rich_text',**serialize_notion('EF-2611-ZZZZ','rich_text')}
    with pytest.raises(IntakeDestinationBlocked):resolver(SOURCE,'EF-2611-ABCD',PAGE)
    assert db.request('__inspect')['submissions'][0]['source_ack_plan'] is None


def test_destination_revision_drift_refuses_source_ack_preparation(db):
    args,c,s,client,resolver=port(db);w=args['workers']
    lease=w.claim(PAGE);w.load(PAGE,lease);row=args['notion'].snapshot(PAGE)
    w.finish(PAGE,lease,row,status='self_write_acknowledged');w.release(PAGE,lease)
    with pytest.raises(RuntimeError):prepare_source_ack(source_page_id=SOURCE,payload_hash=args['payload_hash'],processed=args['processed'],submissions=args['submissions'],resolver=resolver)
    assert db.request('__inspect')['submissions'][0]['source_ack_plan'] is None


def test_changed_source_snapshot_cannot_replace_immutable_ack_plan(db):
    args,c,s,client,resolver=port(db)
    kw=dict(source_page_id=SOURCE,payload_hash=args['payload_hash'],processed=args['processed'],submissions=args['submissions'],resolver=resolver)
    prepare_source_ack(**kw)
    client.source['last_edited_time']='changed'
    with pytest.raises(RuntimeError):prepare_source_ack(**kw)


def test_wrong_candidate_binding_does_not_choose_another_destination(db):
    args,c,s,client,resolver=port(db)
    with pytest.raises(IntakeDestinationBlocked,match='Durable'):resolver(SOURCE,'EF-2611-ZZZZ',SOURCE)


def test_initial_source_binding_lookup_missing_legacy_record_never_infers_identity(db):
    args,c,s=setup(db)
    assert db.request('inventory_v5_intake_binding',source_page_id=SOURCE)=={'found':False}
    assert db.request('__inspect')['submissions']==[]


def test_source_ack_rejects_payload_replacement_and_never_accepts_caller_success_status(db):
    args,c,s,client,resolver=port(db)
    kw=dict(source_page_id=SOURCE,payload_hash=args['payload_hash'],processed={**args['processed'],'status':'Processed'},submissions=args['submissions'],resolver=resolver)
    with pytest.raises(IntakeDestinationBlocked):prepare_source_ack(**{**kw,'payload_hash':'b'*64})
    plan=prepare_source_ack(**kw)
    assert 'Intake Status' not in plan['properties'] and plan['source_status_unresolved']
    assert not plan['source_completion_allowed']



def test_actual_legacy_durable_binding_resolves_before_submission_without_writes(db):
    args,c,s,client,resolver=port(db,save=False)
    db.request('__legacy_binding',source_page_id=SOURCE,listing_id='EF-2611-ABCD',page_id=PAGE,payload_hash=args['payload_hash'])
    assert resolver(SOURCE,'EF-2611-ABCD',PAGE)['unique']
    assert db.request('__inspect')['submissions']==[] and s.count==0


def test_source_ack_prepare_expired_lease_refuses_without_source_success(db):
    args,c,s,client,resolver=port(db)
    plan=prepare_source_ack(source_page_id=SOURCE,payload_hash=args['payload_hash'],processed=args['processed'],submissions=args['submissions'],resolver=resolver)
    record=args['submissions'].call('claim_existing',SOURCE)
    db.request('__expire')
    with pytest.raises(RuntimeError):args['submissions'].call('prepare_source_ack',SOURCE,record['lease_token'],plan=plan)
    assert db.request('__inspect')['submissions'][0]['phase']=='awaiting_source_ack'
