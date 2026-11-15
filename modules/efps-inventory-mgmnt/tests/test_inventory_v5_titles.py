"""Actual title hooks -> Edge -> isolated PostgreSQL, with typed HTTP port."""
from copy import deepcopy
import pytest
from test_inventory_v5_full_ports import DB, Client, PAGE
from src.inventory_v5_titles import CoordinatedTitleRepository, run_coordinated_renumber, TitleBlocked
from src.inventory_v5_repository import V5Repository
from src.inventory_v5_notion import V5NotionPort
from src.inventory_v5_http import V5HttpNotionClient
from src.inventory_v5_adapter import serialize_notion
from src.inventory_v5 import content_hash

PARENT='bccfd4f55e294b269daa093a928f873a'

@pytest.fixture
def db():
    x=DB()
    yield x
    x.close()


def setup(db, response='ok'):
    row={'listing_id':'EF-2611-ABCD','SL number':'old title',
         'Pipeline Status':'Ready to Post','whatsapp_post':'caption must not change','catalog_title':'original catalog'}
    client=Client(row)
    client.schema['SL number']={'id':'title','type':'title'}
    client.row['SL number']={'type':'title',**serialize_notion(row['SL number'],'title')}
    original_get=client.get_page
    client.get_page=lambda page:{**original_get(page),'parent':{'database_id':PARENT}}
    class Response:
        def __init__(self,status,body):self.ok=status==200;self.status_code=status;self.body=body;self.headers={}
        def json(self):return self.body
    class Session:
        def __init__(self):self.patch_count=0;self.receipts_before_readback=False;self.after_patch=lambda:None
        def request(self,method,url,**kw):
            if method=='GET':
                if response=='saved' and self.patch_count:
                    x=db.request('__inspect')
                    if x['state']['active_effect']:
                        self.receipts_before_readback=all(e.get('receipt',{}).get('request_id')=='title-saved-123' for e in [x['state']['active_effect'],x['jobs'][0]['active_effect']])
                return Response(200,client.get_page(PAGE))
            self.patch_count+=1
            client.update_page(PAGE,kw['json']['properties'])
            self.after_patch()
            if response=='timeout':raise TimeoutError('unknown exact remote flight')
            if response=='saved':return Response(503,{'code':'service_unavailable','request_id':'title-saved-123','additional_data':{'retry_guidance':['Read the object again to confirm the saved change.','Do not repeat the write.']}})
            return Response(200,{})
    session=Session()
    http=V5HttpNotionClient(token='synthetic',version='2022-06-28',session=session)
    notion=V5NotionPort(http,client.schema,expected_parent=PARENT)
    db.request('__seed',page_id=PAGE,row=notion.snapshot(PAGE))
    db.request('inventory_v5_reference',worker_operation='seed',seed=[{'page_id':PAGE,'listing_id':row['listing_id']}])
    workers=V5Repository(request=db.request,identity=lambda page:row['listing_id'],mirror=lambda *a,**kw:pytest.fail('title job cannot publish a broad mirror'))
    repo=CoordinatedTitleRepository(request=db.request,workers=workers,notion=notion,
        schema_loader=lambda:deepcopy(client.schema),sealed_schema_hash=content_hash(client.schema))
    notion.bind_dispatch=repo.bind_dispatch;notion.record_receipt=repo.record_receipt
    return repo,notion,client,session,workers


def test_durable_title_hooks_ack_provenance_and_leave_caption_identity_untouched(db):
    repo,n,c,s,w=setup(db)
    result=run_coordinated_renumber(repository=repo,notion=n)
    assert result['status']=='completed' and s.patch_count==1
    state=db.request('__inspect')['state']
    assert state['last_acknowledged_values']['SL number']=='1'
    assert state['field_provenance']['SL number']['last_generated_value']=='1'
    assert state['pending_patch'] is None and state['active_effect'] is None
    assert state['last_acknowledged_values']['catalog_title']=='original catalog'
    assert state['last_acknowledged_values']['whatsapp_post']=='caption must not change'
    assert state['last_acknowledged_values']['listing_id']=='EF-2611-ABCD'
    assert state['lease_token'] is None
    assert list(c.patches[0])==['SL number']


def test_title_dispatch_cannot_overlap_dependency_lease(db):
    repo,n,c,s,w=setup(db);lease=w.claim(PAGE)
    with pytest.raises(TitleBlocked,match='busy'):run_coordinated_renumber(repository=repo,notion=n)
    assert s.patch_count==0
    w.release(PAGE,lease)


@pytest.mark.parametrize('field,value',[('SL number','human title'),('whatsapp_post','human caption')])
def test_unacknowledged_owner_edits_stop_title_job(db,field,value):
    repo,n,c,s,w=setup(db);c.update_page(PAGE,{field:serialize_notion(value,c.schema[field]['type'])})
    with pytest.raises(TitleBlocked,match='Owner edits'):run_coordinated_renumber(repository=repo,notion=n)
    assert s.patch_count==0
    assert db.request('__inspect')['state']['processing_status']=='needs_review'


def test_timeout_keeps_both_durable_barriers_and_blocks_successors(db):
    repo,n,c,s,w=setup(db,'timeout')
    with pytest.raises(TimeoutError):run_coordinated_renumber(repository=repo,notion=n)
    x=db.request('__inspect')
    assert x['state']['active_effect']['dispatch']['effect_id']
    assert x['jobs'][0]['active_effect']['dispatch']==x['state']['active_effect']['dispatch']
    db.request('__expire')
    assert repo.claim()['needs_recovery'] and w.claim(PAGE) is None
    assert s.patch_count==1


def test_saved503_receipt_in_both_scopes_before_readback_no_retry(db):
    repo,n,c,s,w=setup(db,'saved')
    assert run_coordinated_renumber(repository=repo,notion=n)['status']=='completed'
    assert s.patch_count==1 and s.receipts_before_readback
    x=db.request('__inspect')
    assert {i['scope'] for i in x['incidents']}=={'worker','renumber'}
    assert all(i['status']=='completed' for i in x['incidents'])


def test_crash_between_write_and_ack_resumes_durable_ack_without_second_patch(db):
    repo,n,c,s,w=setup(db)
    actual=repo.ack_title
    repo.ack_title=lambda *a:(_ for _ in ()).throw(TimeoutError('crash before ack'))
    with pytest.raises(TimeoutError):run_coordinated_renumber(repository=repo,notion=n)
    x=db.request('__inspect')
    assert x['state']['pending_patch']=={'SL number':'1'} and x['state']['active_effect'] is None
    repo.ack_title=actual;db.request('__expire')
    assert run_coordinated_renumber(repository=repo,notion=n)['status']=='completed'
    assert s.patch_count==1
    assert db.request('__inspect')['state']['pending_patch'] is None


def test_matching_human_rank_does_not_gain_generated_ownership(db):
    repo,n,c,s,w=setup(db)
    c.update_page(PAGE,{'SL number':serialize_notion('1','title')})
    with pytest.raises(TitleBlocked,match='infer'):run_coordinated_renumber(repository=repo,notion=n)
    assert s.patch_count==0
    assert 'SL number' not in db.request('__inspect')['state']['field_provenance']


def test_other_edit_during_patch_retains_pending_ack_and_reports_review(db):
    repo,n,c,s,w=setup(db)
    s.after_patch=lambda:c.update_page(PAGE,{'whatsapp_post':serialize_notion('new human caption','rich_text')})
    with pytest.raises(TitleBlocked,match='mismatch'):run_coordinated_renumber(repository=repo,notion=n)
    x=db.request('__inspect')['state']
    assert x['pending_patch']=={'SL number':'1'} and x['processing_status']=='needs_review'
    assert x['last_acknowledged_values']['SL number']=='old title'
    assert n.snapshot(PAGE)['whatsapp_post']=='new human caption'


def test_changed_schema_seal_or_parent_refuses_title_write(db):
    repo,n,c,s,w=setup(db)
    repo.schema_loader=lambda:{}
    with pytest.raises(TitleBlocked,match='seal'):run_coordinated_renumber(repository=repo,notion=n)
    assert s.patch_count==0


def test_prepare_crash_preserves_provenance_and_resumes_exact_intent(db):
    repo,n,c,s,w=setup(db)
    original=repo.effect
    repo.effect=lambda *a:(_ for _ in ()).throw(TimeoutError('crash before begin/dispatch'))
    with pytest.raises(TimeoutError):run_coordinated_renumber(repository=repo,notion=n)
    state=db.request('__inspect')['state']
    assert state['pending_kind']=='title' and state['active_effect'] is None
    assert 'SL number' not in state['field_provenance']
    assert w.claim(PAGE) is None  # generic dependency cannot consume title intent
    repo.effect=original;db.request('__expire')
    assert run_coordinated_renumber(repository=repo,notion=n)['status']=='completed'
    assert s.patch_count==1


def test_timeout_never_advances_generated_title_provenance(db):
    repo,n,c,s,w=setup(db,'timeout')
    with pytest.raises(TimeoutError):run_coordinated_renumber(repository=repo,notion=n)
    state=db.request('__inspect')['state']
    assert 'SL number' not in state['field_provenance']
    assert state['last_acknowledged_values']['SL number']=='old title'


def test_dependency_cannot_begin_while_title_request_is_inflight(db):
    repo,n,c,s,w=setup(db)
    def check():
        other=V5Repository(request=db.request,identity=w.identity,mirror=lambda *a,**kw:None)
        assert other.claim(PAGE) is None
    s.after_patch=check
    assert run_coordinated_renumber(repository=repo,notion=n)['status']=='completed'


def test_final_ack_rpc_rejects_wrong_readback_and_stale_row_lease(db):
    repo,n,c,s,w=setup(db)
    before=n.snapshot(PAGE);repo.prepare(PAGE,'1',before=before)
    lease=repo.rows[PAGE]['lease']
    with pytest.raises(RuntimeError):w.finish_title(PAGE,lease,{**before,'SL number':'wrong'})
    db.request('__expire')
    with pytest.raises(RuntimeError):w.finish_title(PAGE,lease,{**before,'SL number':'1'})
    # An expired release is intentionally rejected; don't hide that failure.
    repo.rows.clear()


def test_membership_change_during_pass_is_not_claimed_current_complete(db):
    repo,n,c,s,w=setup(db)
    new='12345678-1234-4234-8234-123456789013'
    s.after_patch=lambda:db.request('inventory_v5_reference',worker_operation='activate',page_id=new,listing_id='EF-2611-ABCE')
    result=run_coordinated_renumber(repository=repo,notion=n)
    assert result['status']=='completed_snapshot' and result['membership_current'] is False
    jobs=db.request('__inspect')['jobs']
    assert jobs[0]['status']=='completed' and jobs[1]['status']=='pending'
    assert jobs[1]['ordered_page_ids']==[new,PAGE]


def test_unknown_title_effect_requires_both_exact_operator_recoveries(db):
    from src.inventory_v5_repository import V5RecoveryRepository
    from src.inventory_v5_reconcile import reconcile_effect, Quiescence
    repo,n,c,s,w=setup(db,'timeout')
    with pytest.raises(TimeoutError):run_coordinated_renumber(repository=repo,notion=n)
    db.request('__expire');recovery=V5RecoveryRepository(request=db.request)
    job_id=db.request('__inspect')['jobs'][0]['job_id']
    for scope in ('worker','renumber'):
        args={'scope':scope,'job_id':job_id if scope=='renumber' else None}
        effect=recovery.recovery_snapshot(PAGE,**args)['effect']
        attestation=db.request('__attest',page_id=PAGE,effect=effect,**args)['id']
        reconcile_effect(repository=recovery,notion=n,page_id=PAGE,
            verify_quiescence=lambda **kw:Quiescence('synthetic terminal writer','synthetic terminal remote','synthetic exact request',attestation),**args)
    assert run_coordinated_renumber(repository=repo,notion=n)['status']=='completed'
    assert s.patch_count==1
    assert db.request('__inspect')['state']['pending_patch'] is None


def test_generated_title_webhook_pass_does_not_regenerate_caption(db):
    from src.inventory_v5_worker import process_dependencies
    repo,n,c,s,w=setup(db)
    run_coordinated_renumber(repository=repo,notion=n)
    mirrored=[];w.mirror_port=lambda page,values,**kw:mirrored.append(values)
    out=process_dependencies(PAGE,notion=n,repository=w,
        render_caption=lambda row:pytest.fail('title generated event must not rewrite caption'),
        route_bhk=lambda value:pytest.fail('title generated event must not change routing'))
    assert out['status']=='self_write_acknowledged' and s.patch_count==1
    assert mirrored[0]['SL number']=='1'
