from copy import deepcopy
import pytest
from src.inventory_v5_http import V5HttpNotionClient,V5NotionWriteError
from src.inventory_v5_notion import V5NotionPort

SAVED={'code':'service_unavailable','request_id':'req123','additional_data':{'retry_guidance':['Read the object again to confirm the saved change.','Do not repeat the write.']}}
class Response:
    def __init__(self,status,body):self.status_code=status;self.body=body;self.headers={};self.ok=status==200
    def json(self):return self.body
class Session:
    def __init__(self,responses):self.responses=responses;self.methods=[]
    def request(self,method,*a,**kw):
        self.methods.append(method);result=self.responses.pop(0)
        if isinstance(result,Exception):raise result
        return result

def run(response,current='1',record=True):
    session=Session([response,Response(200,{'properties':{'SL number':{'type':'title','title':[{'text':{'content':current}}]}}})])
    receipts=[]
    client=V5HttpNotionClient(token='synthetic',version='2026-03-11',session=session)
    port=V5NotionPort(client,{'SL number':{'type':'title'}},record_receipt=(lambda p,r:receipts.append(r))if record else None)
    return port,session,receipts

def test_documented_terminal_saved_response_reads_back_without_retry():
    port,session,receipts=run(Response(503,SAVED))
    assert port.patch('page',{'SL number':'1'})['saved_terminal_readback']
    assert session.methods==['PATCH','GET']
    assert receipts[0]['request_id']=='req123'

@pytest.mark.parametrize('status,body',[(503,{'code':'service_unavailable'}),(504,SAVED),(500,SAVED),(503,{'code':'service_unavailable','message':'The change was saved'})])
def test_generic_error_does_not_gain_saved_receipt_authority(status,body):
    port,session,receipts=run(Response(status,body))
    with pytest.raises(V5NotionWriteError):port.patch('page',{'SL number':'1'})
    assert session.methods==['PATCH']

def test_connection_loss_never_retries_or_claims_terminal_state():
    port,session,receipts=run(TimeoutError('unknown transport outcome'))
    with pytest.raises(TimeoutError):port.patch('page',{'SL number':'1'})
    assert not receipts and session.methods==['PATCH']

def test_terminal_saved_readback_conflict_stays_failed():
    port,session,receipts=run(Response(503,SAVED),current='owner edit')
    with pytest.raises(V5NotionWriteError):port.patch('page',{'SL number':'1'})
    assert session.methods==['PATCH','GET'] and receipts

def test_no_durable_receipt_port_does_not_claim_completed_recovery():
    port,session,receipts=run(Response(503,SAVED),record=False)
    with pytest.raises(V5NotionWriteError):port.patch('page',{'SL number':'1'})
    assert session.methods==['PATCH']


@pytest.mark.parametrize('guidance',[
 ['Read the object again to confirm the saved change.'],
 ['Do not repeat the write.'],
 ['Read the object again to confirm the saved change.','Do not repeat the write.','Actually not saved'],
 'Read the object again to confirm the saved change. Do not repeat the write.',
 ['Not saved. Do not repeat the write.'],None])
def test_partial_malformed_or_conflicting_guidance_stays_unknown(guidance):
    body={**SAVED,'additional_data':{'retry_guidance':guidance}}
    port,session,receipts=run(Response(503,body))
    with pytest.raises(V5NotionWriteError):port.patch('page',{'SL number':'1'})
    assert session.methods==['PATCH']

@pytest.mark.parametrize('field,value',[('page_id','other'),('method','GET'),('body_hash','wrong')])
def test_wrong_dispatch_binding_cannot_clear_saved_path(field,value):
    port,session,receipts=run(Response(503,SAVED))
    original=port.client.update_page
    def mismatched(*args):
        try:return original(*args)
        except V5NotionWriteError as error:error.dispatch[field]=value;raise
    port.client.update_page=mismatched
    with pytest.raises(V5NotionWriteError):port.patch('page',{'SL number':'1'})
    assert not receipts and session.methods==['PATCH']


@pytest.mark.parametrize('extra',[None,'saved',[],0])
def test_malformed_additional_data_stays_unknown(extra):
    port,session,receipts=run(Response(503,{**SAVED,'additional_data':extra}))
    with pytest.raises(V5NotionWriteError):port.patch('page',{'SL number':'1'})
    assert session.methods==['PATCH']
