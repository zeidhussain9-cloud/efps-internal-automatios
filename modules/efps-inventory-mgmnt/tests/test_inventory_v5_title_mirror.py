from copy import deepcopy
import pytest
from test_inventory_v5_titles import setup,db,PAGE,PARENT
from src.inventory_v5_titles import run_coordinated_renumber,CoordinatedTitleRepository
from src.inventory_v5_repository import V5Repository
from src.inventory_v5_notion import V5NotionPort
from src.inventory_v5_http import V5HttpNotionClient
from src.inventory_v5 import content_hash


def test_atomic_title_ack_changes_only_title_revision_and_owned_sync_metadata(db):
    repo,n,c,s,w=setup(db)
    db.request('__title_mirror_mutate',annotation={'operator_annotation':{'keep':'untouched'}})
    before=db.request('__inspect')['mirror']
    assert run_coordinated_renumber(repository=repo,notion=n)['status']=='completed'
    x=db.request('__inspect');after=x['mirror'];expected=deepcopy(before)
    expected['source_record']['SL number']='1';expected['inventory_revision']=2;expected['last_synced_at']=after['last_synced_at'];expected['source_hash']=after['source_hash']
    assert after['source_hash']!=before['source_hash'] and len(after['source_hash'])==64
    assert after==expected and x['state']['revision']==2 and after['source_record']['operator_annotation']=={'keep':'untouched'}
    assert after['source_record']['SL number']==x['state']['last_acknowledged_values']['SL number']=='1'


@pytest.mark.parametrize('bad',['missing','deleted','wrong_binding','wrong_kind','ahead','quarantine','wrong_status'])
def test_invalid_mirror_refuses_before_title_http_and_never_gains_provenance(db,bad):
    repo,n,c,s,w=setup(db)
    if bad=='missing':db.request('__title_mirror_mutate',remove=True)
    elif bad=='wrong_binding':db.request('__title_mirror_mutate',annotation={'notion_page_id':'wrong-page'})
    elif bad=='quarantine':db.request('__title_mirror_mutate',annotation={'intake_conflict_quarantined':True})
    else:
        change={'deleted':{'deleted_at':'2026-11-15T00:00:00Z'},'wrong_kind':{'source_kind':'elsewhere'},
          'ahead':{'inventory_revision':2},'wrong_status':{'pipeline_status':'Needs Review'}}[bad]
        db.request('__title_mirror_mutate',change=change)
    with pytest.raises(RuntimeError):run_coordinated_renumber(repository=repo,notion=n)
    x=db.request('__inspect');assert s.patch_count==0 and 'SL number'not in x['state']['field_provenance']
    assert x['state']['pending_patch'] is None


def test_mirror_annotation_change_after_prepare_holds_after_visible_title_without_ack(db):
    repo,n,c,s,w=setup(db)
    s.after_patch=lambda:db.request('__title_mirror_mutate',annotation={'new_owner_annotation':'preserve'})
    with pytest.raises(RuntimeError):run_coordinated_renumber(repository=repo,notion=n)
    x=db.request('__inspect')
    assert s.patch_count==1 and n.snapshot(PAGE)['SL number']=='1'
    assert x['state']['last_acknowledged_values']['SL number']=='old title' and x['state']['pending_kind']=='title'
    assert 'SL number'not in x['state']['field_provenance']
    assert x['mirror']['source_record']['SL number']=='old title' and x['mirror']['source_record']['new_owner_annotation']=='preserve'


def test_mirror_update_failure_rolls_back_title_ack_and_provenance_then_resumes_no_patch(db):
    repo,n,c,s,w=setup(db);db.request('__fail_title_mirror',enabled=True)
    with pytest.raises(RuntimeError):run_coordinated_renumber(repository=repo,notion=n)
    x=db.request('__inspect');assert x['state']['revision']==1 and x['mirror']['inventory_revision']==0
    assert x['state']['pending_title_mirror'] and 'SL number'not in x['state']['field_provenance']
    db.request('__fail_title_mirror',enabled=False);db.request('__expire')
    assert run_coordinated_renumber(repository=repo,notion=n)['status']=='completed' and s.patch_count==1
    x=db.request('__inspect');assert x['state']['revision']==x['mirror']['inventory_revision']==2


def test_atomic_finish_response_loss_replay_checks_mirror_and_never_patches_twice(db):
    repo,n,c,s,w=setup(db);orig=w.finish_title
    def lost(*a):value=orig(*a);raise TimeoutError('atomic title finish response lost')
    w.finish_title=lost
    with pytest.raises(TimeoutError):run_coordinated_renumber(repository=repo,notion=n)
    x=db.request('__inspect');assert x['state']['revision']==x['mirror']['inventory_revision']==2
    w.finish_title=orig;db.request('__expire')
    assert run_coordinated_renumber(repository=repo,notion=n)['status']=='completed' and s.patch_count==1


def test_replay_does_not_skip_corrupted_mirror_after_atomic_finish(db):
    repo,n,c,s,w=setup(db);orig=w.finish_title
    def lost(*a):orig(*a);raise TimeoutError('atomic finish response lost')
    w.finish_title=lost
    with pytest.raises(TimeoutError):run_coordinated_renumber(repository=repo,notion=n)
    db.request('__title_mirror_mutate',annotation={'SL number':'stale'},change={'inventory_revision':3})
    w.finish_title=orig;db.request('__expire')
    with pytest.raises(RuntimeError):run_coordinated_renumber(repository=repo,notion=n)
    assert s.patch_count==1 and db.request('__inspect')['jobs'][0]['status']=='running'


def test_created_fixture_row1_mirror1_blank_title_uses_same_atomic_hooks(db,monkeypatch):
    from test_inventory_v5_create import setup as create_setup
    from src.inventory_v5_create import create_fixture
    args,c,create_session,counts=create_setup(db,monkeypatch);created=create_fixture(**args)
    listing_id=created['listing_id']
    class Session:
        count=0
        def request(self,method,url,**kw):
            class Response:
                ok=True;status_code=200;headers={}
                def __init__(self,body):self.body=body
                def json(self):return deepcopy(self.body)
            if method=='GET':return Response(c.get_page(PAGE))
            self.count+=1
            for k,v in kw['json']['properties'].items():c.page['properties'][k].update(deepcopy(v))
            return Response({})
    session=Session();http=V5HttpNotionClient(token='synthetic',version='2022-06-28',session=session)
    notion=V5NotionPort(http,args['schema_loader'](),expected_parent=PARENT)
    workers=V5Repository(request=db.request,identity=lambda page:listing_id,mirror=lambda *a,**kw:pytest.fail('no broad mirror'))
    repo=CoordinatedTitleRepository(request=db.request,workers=workers,notion=notion,schema_loader=args['schema_loader'],sealed_schema_hash=args['sealed_schema_hash'])
    assert run_coordinated_renumber(repository=repo,notion=notion)['status']=='completed'
    x=db.request('__inspect');assert x['state']['revision']==x['mirror']['inventory_revision']==2
    assert x['mirror']['source_record']['SL number']=='1' and x['mirror']['pipeline_status']=='Processing'
    assert all(v['origin']=='legacy_unknown'for k,v in x['state']['field_provenance'].items()if k!='SL number')
    assert x['state']['field_provenance']['SL number']['origin']=='derived'
    assert c.source['properties']['Processed Property']['relation']==[] and x['creations'][0]['phase']=='bootstrapped'
    assert create_session.count==1 and session.count==1


def test_frozen_mirror_proof_survives_prepare_response_loss_and_is_not_refreshed(db):
    repo,n,c,s,w=setup(db);orig=w.prepare_title
    def lost(*a,**kw):orig(*a,**kw);raise TimeoutError('prepare response lost')
    w.prepare_title=lost
    with pytest.raises(TimeoutError):run_coordinated_renumber(repository=repo,notion=n)
    frozen=db.request('__inspect')['state']['pending_title_mirror']
    db.request('__title_mirror_mutate',annotation={'external_annotation':'changed after prepare'})
    w.prepare_title=orig;db.request('__expire')
    with pytest.raises(RuntimeError):run_coordinated_renumber(repository=repo,notion=n)
    x=db.request('__inspect');assert x['state']['pending_title_mirror']==frozen and x['state']['revision']==1
    assert 'SL number'not in x['state']['field_provenance'] and s.patch_count==1


def test_already_numbered_unchanged_baseline_verifies_mirror_without_ownership_promotion(db):
    repo,n,c,s,w=setup(db)
    # Install a valid initially numbered baseline, not an unacknowledged edit.
    before=n.snapshot(PAGE);token=w.claim(PAGE);w.load(PAGE,token)
    c.update_page(PAGE,{'SL number':{'title':[{'type':'text','text':{'content':'1'}}]}})
    current=n.snapshot(PAGE);w.finish(PAGE,token,current,status='self_write_acknowledged');w.release(PAGE,token)
    # Same-version mirror revision1 is valid against row2 only when its baseline
    # really contains the acknowledged title. Test helper mutation advances0->1.
    db.request('__title_mirror_mutate',title='1')
    assert run_coordinated_renumber(repository=repo,notion=n)['status']=='completed'
    assert s.patch_count==0 and 'SL number'not in db.request('__inspect')['state']['field_provenance']
