"""Real repository -> actual Edge handler -> disposable PostgreSQL integration."""
import json
import subprocess
from pathlib import Path
from copy import deepcopy
import pytest
from src.inventory_v5_repository import V5Repository,V5RenumberRepository
from src.inventory_v5_notion import V5NotionPort
from src.inventory_v5_adapter import serialize_notion
from src.inventory_v5_worker import process_dependencies
from src.inventory_v5 import content_hash

PAGE='12345678-1234-4234-8234-123456789012'
ROOT=Path(__file__).resolve().parents[3]

class DB:
    def __init__(self):
        self.p=subprocess.Popen(['node','tests/helpers/inventory-v5-bridge.mjs'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    def request(self,operation,**body):
        self.p.stdin.write(json.dumps({'operation':operation,**body})+'\n');self.p.stdin.flush()
        line=self.p.stdout.readline()
        if not line:raise RuntimeError('Bridge exited: '+self.p.stderr.read())
        value=json.loads(line)
        if 'error'in value:raise RuntimeError(value['error'])
        return value['result']
    def close(self):
        self.p.stdin.close();self.p.wait(timeout=10)
        assert self.p.returncode==0,self.p.stderr.read()
        self.p.stdout.close();self.p.stderr.close()

class Client:
    def __init__(self,row):
        self.schema={name:{'id':name,'type':('number'if name in ('built_up_area','carpet_area')else 'rich_text')}for name in row}
        self.schema['Pipeline Status']={'id':'pipe','type':'select','select':{'options':[{'name':'Ready to Post'},{'name':'Needs Review'}]}}
        self.row={name:{'type':definition['type'],**serialize_notion(row[name],definition['type'])}for name,definition in self.schema.items()}
        self.patches=[]
    def get_page(self,page):return {'properties':deepcopy(self.row),'archived':False,'last_edited_time':'same'}
    def update_page(self,page,properties):
        self.patches.append(properties)
        self.row.update({key:{'type':self.schema[key]['type'],**value}for key,value in properties.items()})

@pytest.fixture
def db():
    value=DB()
    yield value
    value.close()

def setup(db,edit=None):
    before={'listing_id':'EF-2611-ABCD','Pipeline Status':'Ready to Post','raw_message_text':'old'}
    # Real typed page snapshots have numeric version only in the mirror contract.
    client=Client(before);notion=V5NotionPort(client,client.schema);ack=notion.snapshot(PAGE)
    db.request('__seed',page_id=PAGE,row=ack)
    repo=V5Repository(request=db.request,identity=lambda page:before['listing_id'],mirror=lambda *args,**kwargs:None)
    if edit:
        client.update_page(PAGE,{key:serialize_notion(value,client.schema[key]['type'])for key,value in edit.items()})
    return repo,notion,client

def test_identity_edit_quarantines_real_known_mirror_and_durable_status(db):
    repo,notion,client=setup(db,{'listing_id':'EF-2611-ZZZZ'})
    result=process_dependencies(PAGE,notion=notion,repository=repo,render_caption=lambda row:'unused',route_bhk=lambda bhk:('',''))
    assert result['status']=='needs_review'
    final=db.request('__inspect')
    assert final['state']['processing_status']=='needs_review'
    assert final['state']['field_provenance']['listing_id']['origin']=='manual'
    assert final['mirror']['listing_id']=='EF-2611-ABCD'
    assert final['mirror']['pipeline_status']=='Needs Review'
    assert final['mirror']['business_status']=='Needs Review'
    assert final['mirror']['source_record']['listing_id']=='EF-2611-ABCD'
    assert notion.snapshot(PAGE)['listing_id']=='EF-2611-ZZZZ'
    assert notion.snapshot(PAGE)['Pipeline Status']=='Needs Review'

def test_inflight_expiry_blocks_successor_and_never_auto_replays(db):
    repo,notion,client=setup(db)
    lease=repo.claim(PAGE);repo.load(PAGE,lease)
    seen=[]
    def delayed_effect():
        db.request('__expire')
        competitor=db.request('inventory_v5_worker',page_id=PAGE,worker_operation='claim',listing_id='EF-2611-ABCD')
        assert competitor['needs_recovery'] and competitor['busy']
        seen.append('effect completed after expiry')
    with pytest.raises(RuntimeError):repo.effect(PAGE,lease,{'kind':'notion_patch','patch':{'x':1}},delayed_effect)
    assert seen
    final=db.request('__inspect')
    assert final['state']['active_effect']['intent']['patch']=={'x':1}
    assert final['mirror']['source_hash']=='seed'
    assert repo.claim(PAGE) is None

def test_expired_worker_cannot_begin_external_effect(db):
    repo,notion,client=setup(db)
    lease=repo.claim(PAGE);repo.load(PAGE,lease);db.request('__expire')
    seen=[]
    with pytest.raises(RuntimeError):repo.effect(PAGE,lease,{'kind':'notion_patch'},lambda:seen.append(True))
    assert not seen


def test_typed_numeric_write_readback_and_second_pass_use_actual_mirror(db):
    before={'listing_id':'EF-2611-ABCD','Pipeline Status':'Ready to Post','built_up_area':1200,'carpet_area':1110,'whatsapp_post':'old caption'}
    client=Client(before);notion=V5NotionPort(client,client.schema)
    provenance={'carpet_area':{'origin':'derived','last_generated_value':'1110'},'whatsapp_post':{'origin':'derived','last_generated_value':'old caption'}}
    db.request('__seed',page_id=PAGE,row=notion.snapshot(PAGE),provenance=provenance)
    def mirror(page,values,*,deleted,lease,revision):
        row={**values,'inventory_contract_version':5,'Availability':'Available','Live On':[],'onboarded_at':'2026-11-15T09:11:00Z'}
        return db.request('sync_inventory',page_id=page,listing_id=row['listing_id'],row=row,deleted=deleted,lease=lease,revision=revision,source_hash=content_hash(row))
    repo=V5Repository(request=db.request,identity=lambda page:before['listing_id'],mirror=mirror)
    for built_up,carpet in ((1300,1210),(1400,1310)):
        client.update_page(PAGE,{'built_up_area':serialize_notion(built_up,'number')})
        out=process_dependencies(PAGE,notion=notion,repository=repo,render_caption=lambda row:'new caption',route_bhk=lambda bhk:('',''))
        assert out['status']=='recalculated'
        assert notion.snapshot(PAGE)['carpet_area']==carpet
        final=db.request('__inspect')
        assert final['mirror']['source_record']['carpet_area']==carpet
        assert final['state']['field_provenance']['carpet_area']['last_generated_value']==str(carpet)


def test_interrupted_typed_numeric_patch_replay_real_ports(db):
    row={'listing_id':'EF-2611-ABCD','Pipeline Status':'Ready to Post','built_up_area':1300,'carpet_area':1110,'whatsapp_post':'old caption'}
    client=Client(row);notion=V5NotionPort(client,client.schema)
    prepared=notion.snapshot(PAGE)
    db.request('__seed',page_id=PAGE,row=prepared)
    def mirror(page,values,*,deleted,lease,revision):
        row={**values,'inventory_contract_version':5,'Availability':'Available','Live On':[],'onboarded_at':'2026-11-15T09:11:00Z'}
        return db.request('sync_inventory',page_id=page,listing_id=row['listing_id'],row=row,deleted=deleted,lease=lease,revision=revision,source_hash=content_hash(row))
    repo=V5Repository(request=db.request,identity=lambda page:row['listing_id'],mirror=mirror)
    lease=repo.claim(PAGE);state=repo.load(PAGE,lease)
    repo.prepare(PAGE,lease,expected_revision=state['revision'],input_hash=content_hash(prepared),input_values=prepared,patch={'carpet_area':'1210','whatsapp_post':'new caption'},provenance={})
    repo.effect(PAGE,lease,{'kind':'notion_patch'},lambda:notion.patch(PAGE,{'carpet_area':'1210'}))
    repo.release(PAGE,lease)
    out=process_dependencies(PAGE,notion=notion,repository=repo,render_caption=lambda row:'unused',route_bhk=lambda bhk:('',''))
    assert out['status']=='recovered'
    assert notion.snapshot(PAGE)['carpet_area']==1210
    assert notion.snapshot(PAGE)['whatsapp_post']=='new caption'
    assert db.request('__inspect')['mirror']['source_record']['carpet_area']==1210


def test_renumber_inflight_effect_fences_real_successor(db):
    db.request('inventory_v5_reference',worker_operation='seed',seed=[{'page_id':PAGE,'listing_id':'EF-2611-ABCD'}])
    repo=V5RenumberRepository(request=db.request,prepare_title=lambda *a:None,ack_title=lambda *a:None)
    job=repo.claim();seen=[]
    def late_title_write():
        db.request('__expire')
        other=repo.claim()
        assert other['busy'] and other['needs_recovery']
        seen.append('late title write completed without successor overlap')
    with pytest.raises(RuntimeError):repo.effect(job['job_id'],job['lease_token'],{'page_id':PAGE,'patch':{'SL number':'1'}},late_title_write)
    assert seen
    assert repo.claim()['needs_recovery']
