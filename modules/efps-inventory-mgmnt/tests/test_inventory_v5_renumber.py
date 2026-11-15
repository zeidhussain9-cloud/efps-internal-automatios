from copy import deepcopy
from src.inventory_v5_renumber import run_renumber
class N:
    def __init__(self):self.rows={'a':{'SL number':'old A','listing_id':'A'},'b':{'SL number':'old B','listing_id':'B'}};self.patches=[]
    def snapshot(self,page):return deepcopy(self.rows[page])
    def patch(self,page,p):self.patches.append((page,p));self.rows[page].update(p)
class R:
    def __init__(self):self.offset=0;self.done=False;self.calls=[]
    def claim(self):return {'ordered_page_ids':['a','b'],'next_offset':self.offset,'lease_token':'lease','job_id':1}
    def renew(self,*a):self.calls.append('renew')
    def checkpoint(self,j,l,x):self.offset=x
    def prepare_title(self,*a):self.calls.append('prepare')
    def ack_title(self,*a):self.calls.append('ack')
    def finish(self,*a):self.done=True
    def yield_lease(self,*a):self.calls.append('yield')
    def fail(self,*a):self.calls.append('fail')
def test_resumable_reference_titles_only_no_identity_or_caption_writes():
    n=N();r=R();out=run_renumber(repository=r,notion=n,max_rows=1)
    assert out['status']=='paused' and r.offset==1 and not r.done
    out=run_renumber(repository=r,notion=n,max_rows=1)
    assert out['status']=='completed' and r.done
    assert n.patches==[('a',{'SL number':'1'}),('b',{'SL number':'2'})]
    assert n.rows['a']['listing_id']=='A'
def test_retry_of_already_applied_title_is_idempotent():
    n=N();n.rows['a']['SL number']='1';r=R()
    run_renumber(repository=r,notion=n)
    assert n.patches==[('b',{'SL number':'2'})]
def test_deleted_member_stops_and_does_not_renumber_rest():
    n=N();n.rows['a']['_archived']=True;r=R()
    assert run_renumber(repository=r,notion=n)['status']=='membership_changed'
    assert not n.patches and 'fail' in r.calls
