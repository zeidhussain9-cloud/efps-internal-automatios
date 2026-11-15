from src.inventory_v5_repository import V5Repository

def test_repository_maps_durable_fields_and_threads_lease():
    calls=[]
    def request(op,**values):
        calls.append((op,values))
        if values['worker_operation']=='claim':return {'lease':'lease1'}
        if values['worker_operation']=='load':return {'last_acknowledged_values':{'BHK':'2 BHK'},'field_provenance':{},'source_evidence':{},'revision':3,'pending_patch':{'x':1},'prepared_inputs':{'x':0}}
        return {'ok':True}
    repo=V5Repository(request=request,identity=lambda page:'EF-2611-ABCD',mirror=lambda *a,**k:None)
    assert repo.claim('page')=='lease1'
    state=repo.load('page','lease1');assert state['revision']==3;assert state['pending_patch']=={'x':1}
    repo.prepare('page','lease1',expected_revision=3,input_hash='a'*64,input_values={'x':0},patch={'x':1},provenance={})
    repo.review('page',['x'],'conflict');repo.finish('page','lease1',{'x':1},status='recalculated');repo.release('page','lease1')
    assert all(c[0]=='inventory_v5_worker' for c in calls)
    assert calls[2][1]['revision']==3 and calls[2][1]['values']=={'x':0}
    assert calls[3][1]['lease']=='lease1'
    assert not repo.leases
