from copy import deepcopy
from src.inventory_v5_worker import process_dependencies

class Notion:
    def __init__(self,row):self.row=deepcopy(row);self.patches=[];self.reads=0;self.edit_on_second=None
    def snapshot(self,page):
        self.reads+=1
        if self.reads==2 and self.edit_on_second:self.row.update(self.edit_on_second)
        return deepcopy(self.row)
    def patch(self,page,patch):self.patches.append(deepcopy(patch));self.row.update(patch)

class Repo:
    def __init__(self,before,provenance=None,expected=None):
        self.state={'acknowledged':before,'provenance':provenance or {},'revision':1,'expected_self_write':expected};self.calls=[]
    def claim(self,page):self.calls.append('claim');return 'lease'
    def load(self,*a):return deepcopy(self.state)
    def mirror(self,*a,**k):self.calls.append('mirror')
    def finish(self,*a,**k):self.calls.append('finish')
    def review(self,*a):self.calls.append('review')
    def prepare(self,*a,**kw):self.calls.append('prepare');self.prepared=kw
    def requeue(self,*a,**k):self.calls.append('requeue')
    def renew(self,*a):self.calls.append('renew')
    def release(self,*a):self.calls.append('release')

def run(n,r):return process_dependencies('page',notion=n,repository=r,render_caption=lambda row:'new caption',route_bhk=lambda bhk:('group','destination'))

def test_derived_change_narrow_patch_and_intent_before_effect():
    before={'furnish_type':'Semi Furnished','flat_furnishings':'Semi Package','whatsapp_post':'old caption'}
    n=Notion({**before,'furnish_type':'Fully Furnished'})
    r=Repo(before,{'flat_furnishings':{'origin':'derived','last_generated_value':'Semi Package'},'whatsapp_post':{'origin':'derived','last_generated_value':'old caption'}})
    out=run(n,r)
    assert out['status']=='recalculated'
    assert n.patches==[{'flat_furnishings':'Full Package','whatsapp_post':'new caption'}]
    assert r.calls.index('prepare')<r.calls.index('mirror')
    assert r.calls[-1]=='release'

def test_manual_child_stays_and_gets_review():
    before={'furnish_type':'Semi Furnished','flat_furnishings':'Custom','whatsapp_post':'Owner caption'}
    n=Notion({**before,'furnish_type':'Fully Furnished'});r=Repo(before)
    out=run(n,r)
    assert out['status']=='needs_review'
    assert n.row['flat_furnishings']=='Custom'
    assert n.row['whatsapp_post']=='Owner caption'
    assert n.row['Pipeline Status']=='Needs Review'

def test_concurrent_edit_before_patch_is_not_overwritten():
    before={'furnish_type':'Semi Furnished','flat_furnishings':''}
    n=Notion({**before,'furnish_type':'Fully Furnished'});n.edit_on_second={'flat_furnishings':'Owner update'}
    r=Repo(before)
    out=run(n,r)
    assert out['status']=='retry'
    assert not n.patches
    assert 'prepare' not in r.calls

def test_title_only_renumber_does_not_derive_caption():
    before={'SL number':'1','whatsapp_post':'Owner caption'}
    n=Notion({**before,'SL number':'2'});r=Repo(before,expected={'SL number':'2'})
    out=run(n,r)
    assert out['status']=='self_write_acknowledged'
    assert not n.patches

def test_deleted_row_only_tombstones_mirror():
    n=Notion({'_archived':True});r=Repo({})
    out=run(n,r)
    assert out['status']=='deleted'
    assert not n.patches
    assert r.calls==['claim','mirror','finish','release']

def test_explicit_blank_manual_value_is_protected():
    before={'internal_property_type':'Gated Community','society_amenities':''}
    n=Notion({**before,'internal_property_type':'Semi Gated'})
    r=Repo(before,{'society_amenities':{'origin':'manual'}})
    out=run(n,r)
    assert out['status']=='needs_review'
    assert n.row['society_amenities']==''

def test_completed_self_write_advances_generated_provenance():
    before={'furnish_type':'Semi Furnished','flat_furnishings':'Semi Package','whatsapp_post':'old caption'}
    n=Notion({**before,'furnish_type':'Fully Furnished'})
    r=Repo(before,{'flat_furnishings':{'origin':'derived','last_generated_value':'Semi Package'},'whatsapp_post':{'origin':'derived','last_generated_value':'old caption'}})
    run(n,r)
    assert r.prepared['provenance']['flat_furnishings']['last_generated_value']=='Full Package'
    assert r.prepared['input_values']['flat_furnishings']=='Semi Package'

def test_interrupted_partial_write_replays_only_missing_values():
    prepared={'furnish_type':'Fully Furnished','flat_furnishings':'Semi Package','whatsapp_post':'old caption'}
    n=Notion({**prepared,'flat_furnishings':'Full Package'});r=Repo({})
    r.state.update(pending_patch={'flat_furnishings':'Full Package','whatsapp_post':'new caption'},prepared_inputs=prepared)
    out=run(n,r)
    assert out['status']=='recovered'
    assert n.patches==[{'whatsapp_post':'new caption'}]

def test_interrupted_write_with_human_third_value_never_replays():
    prepared={'furnish_type':'Fully Furnished','flat_furnishings':'Semi Package','whatsapp_post':'old caption'}
    n=Notion({**prepared,'flat_furnishings':'Owner choice'});r=Repo({})
    r.state.update(pending_patch={'flat_furnishings':'Full Package'},prepared_inputs=prepared)
    out=run(n,r)
    assert out['status']=='needs_review'
    assert not n.patches

def test_protected_edit_persists_needs_review_not_just_return_value():
    before={'listing_id':'EF-2611-ABCD','raw_message_text':'old','Pipeline Status':'Ready to Post'}
    n=Notion({**before,'raw_message_text':'owner new source'});r=Repo(before)
    out=run(n,r)
    assert out['status']=='needs_review'
    assert n.row['Pipeline Status']=='Needs Review'
    assert n.row['raw_message_text']=='owner new source'
    assert n.patches==[{'Pipeline Status':'Needs Review'}]

def test_changed_identity_never_mirrors_under_unverified_identity():
    before={'listing_id':'EF-2611-ABCD','Pipeline Status':'Ready to Post'}
    n=Notion({**before,'listing_id':'EF-2611-ZZZZ'});r=Repo(before)
    out=run(n,r)
    assert out['status']=='needs_review' and n.row['Pipeline Status']=='Needs Review'
    assert 'mirror' not in r.calls

def test_notion_numeric_readback_acknowledges_string_intent():
    class NumericNotion(Notion):
        def patch(self,page,patch):
            self.patches.append(deepcopy(patch))
            self.row.update({k:float(v)if k=='carpet_area' else v for k,v in patch.items()})
    before={'built_up_area':1200,'carpet_area':1110,'whatsapp_post':'old caption'}
    n=NumericNotion({**before,'built_up_area':1300});r=Repo(before,{'carpet_area':{'origin':'derived','last_generated_value':1110},'whatsapp_post':{'origin':'derived','last_generated_value':'old caption'}})
    out=run(n,r)
    assert out['status']=='recalculated'
    assert n.row['carpet_area']==1210
