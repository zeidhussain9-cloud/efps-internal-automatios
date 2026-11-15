from copy import deepcopy
import pytest
from src.inventory_v5_reconcile import RecoveryBlocked,Quiescence,reconcile_effect

class Repository:
    def __init__(self):
        self.state={'effect':{'intent':{'patch':{'x':2,'caption':'new'}},'lease':'old'},'prepared_inputs':{'x':1,'caption':'old'}}
        self.resolved=[];self.change_during_read=False
    def recovery_snapshot(self,*a,**k):return deepcopy(self.state)
    def resolve_effect(self,*a,expected_effect,**k):
        if self.state['effect']!=expected_effect:raise RecoveryBlocked('Effect changed before atomic compare')
        self.resolved.append(k);self.state['effect']=None;return {'status':'reconciled_without_notion_write'}
class Notion:
    def __init__(self,row):self.row=row;self.reads=0
    def snapshot(self,page):self.reads+=1;return deepcopy(self.row)

def proof(**kwargs):return Quiescence('verified worker termination log','verified remote terminal response','exact request123','attestation123')
def run(r,n,**kw):return reconcile_effect(repository=r,notion=n,page_id='p',scope='worker',**kw)

@pytest.mark.parametrize('claim',['lease expired','HTTP timed out','process dead','unchanged readback'])
def test_default_verifier_never_clears_from_timeout_or_plausible_claim(claim):
    r=Repository();n=Notion({'x':2,'caption':'new'})
    with pytest.raises(RecoveryBlocked):run(r,n)
    assert r.state['effect']is not None and not r.resolved and n.reads==0

def test_proven_terminal_partial_readback_prepares_resume_without_writing():
    r=Repository();n=Notion({'x':2,'caption':'old'})
    assert run(r,n,verify_quiescence=proof)['status']=='reconciled_without_notion_write'
    assert r.resolved[0]['remaining']=={'caption':'new'}

def test_missing_either_independent_proof_reference_blocks():
    r=Repository();n=Notion({'x':2,'caption':'new'})
    with pytest.raises(RecoveryBlocked):run(r,n,verify_quiescence=lambda **k:Quiescence('process terminated','','request','id'))
    assert not r.resolved

def test_third_value_requires_review_not_replay_or_clear():
    r=Repository();n=Notion({'x':8,'caption':'owner edit'})
    with pytest.raises(RecoveryBlocked):run(r,n,verify_quiescence=proof)
    assert not r.resolved and r.state['effect']

def test_changed_ticket_cannot_be_cleared_by_old_reconciliation():
    r=Repository();n=Notion({'x':2,'caption':'new'})
    def verifier(**kwargs):r.state['effect']['lease']='different';return proof()
    with pytest.raises(RecoveryBlocked):run(r,n,verify_quiescence=verifier)
    assert not r.resolved
