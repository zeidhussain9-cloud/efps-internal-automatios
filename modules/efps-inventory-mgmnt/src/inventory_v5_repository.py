"""Fenced SQL state via the existing authenticated Edge transport.

The transport is injected; this module holds no credentials and opens no socket.
Not yet enabled in the production webhook.
"""
from __future__ import annotations

class V5Repository:
    def __init__(self, *, request, identity, mirror):
        self.request=request;self.identity=identity;self.mirror_port=mirror;self.leases={};self.revisions={};self.blocked_state={}

    def _call(self, operation, page, lease=None, **values):
        return self.request('inventory_v5_worker',page_id=page,
            worker_operation=operation,listing_id=self.identity(page),lease=lease,**values)

    def claim(self,page):
        result=self._call('claim',page)
        self.blocked_state[page]=result if result.get('needs_recovery') else {}
        lease=result.get('lease')
        if lease:self.leases[page]=lease
        return lease

    def load(self,page,lease):
        row=self._call('load',page,lease)
        self.revisions[page]=row['revision']
        return {'acknowledged':row['last_acknowledged_values'],
            'provenance':row['field_provenance'],'source_evidence':row['source_evidence'],
            'expected_self_write':row.get('expected_self_write'),
            'pending_patch':row.get('pending_patch'),'prepared_inputs':row.get('prepared_inputs'),
            'revision':row['revision']}

    def prepare(self,page,lease,*,expected_revision,input_hash,input_values,patch,provenance):
        return self._call('prepare',page,lease,revision=expected_revision,input_hash=input_hash,
                         values=input_values,patch=patch,provenance=provenance)

    def review(self,page,fields,reason):
        return self._call('review',page,self.leases[page],review={'fields':fields,'reason':reason})

    def finish(self,page,lease,values,*,status):
        return self._call('finish',page,lease,values=values,status=status)

    def mirror(self,page,values,*,deleted):
        # The Edge/SQL mirror port must pass these into inventory_v5_sync_snapshot.
        return self.mirror_port(page,values,deleted=deleted,lease=self.leases[page],revision=self.revisions[page])

    def quarantine_identity(self,page,lease):
        result=self.request('inventory_v5_quarantine_identity',page_id=page,lease=lease)
        self.revisions[page]=result['revision']
        return result

    def requeue(self,page,lease,*,reason):
        return self._call('requeue',page,lease,status=reason)

    def record_receipt(self,page,receipt):
        return self._call('record_effect_receipt',page,self.leases[page],values=receipt)

    def effect(self,page,lease,intent,action):
        # An expired owner cannot start an effect. Once started, durable active_effect
        # blocks takeover even after lease expiry. Any timeout/error leaves it there
        # for explicit readback/reconciliation, never automatic overlapping replay.
        self.renew(page,lease)
        self._call('begin_effect',page,lease,values=intent)
        self.renew(page,lease)
        result=action()
        self._call('end_effect',page,lease)
        return result

    def renew(self,page,lease):return self._call('renew',page,lease)

    def release(self,page,lease):
        try:return self._call('release',page,lease)
        finally:self.leases.pop(page,None)


class V5RenumberRepository:
    """Staged title-job port. Title provenance hooks stay separately injected."""
    def __init__(self,*,request,prepare_title,ack_title):
        self.request=request;self.prepare_title=prepare_title;self.ack_title=ack_title

    def _call(self,operation,job=None,lease=None,**values):
        return self.request('inventory_v5_renumber',worker_operation=operation,job_id=job,lease=lease,**values)

    def claim(self):return self._call('claim')
    def renew(self,job,lease):return self._call('renew',job,lease)
    def checkpoint(self,job,lease,offset):return self._call('checkpoint',job,lease,next_offset=offset)
    def finish(self,job,lease):return self._call('finish',job,lease)
    def yield_lease(self,job,lease):return self._call('yield',job,lease)
    def fail(self,job,lease,error):return self._call('fail',job,lease,error=error)

    def effect(self,job,lease,intent,action):
        import json
        self.renew(job,lease)
        self._call('begin_effect',job,lease,error=json.dumps(intent,separators=(',',':')))
        self.renew(job,lease)
        result=action()
        self._call('end_effect',job,lease)
        return result


class V5RecoveryRepository:
    """Operator recovery port. Ordinary workers cannot mint attestations."""
    def __init__(self,*,request):self.request=request

    def recovery_snapshot(self,page,*,scope,job_id=None):
        return self.request('inventory_v5_recovery_snapshot',page_id=page,scope=scope,job_id=job_id)

    def resolve_effect(self,page,*,scope,job_id,expected_effect,current,remaining,proof,state_hash):
        return self.request('inventory_v5_recover_effect',page_id=page,scope=scope,job_id=job_id,
            attestation_id=proof['attestation_id'],expected_effect=expected_effect,current=current,remaining=remaining,
            state_hash=state_hash,decision={'proof':proof,'result':'recognized_partial'if remaining else'fully_applied','notion_write':False})
