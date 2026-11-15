"""Fenced SQL state via the existing authenticated Edge transport.

The transport is injected; this module holds no credentials and opens no socket.
Not yet enabled in the production webhook.
"""
from __future__ import annotations

class V5Repository:
    def __init__(self, *, request, identity, mirror):
        self.request=request;self.identity=identity;self.mirror_port=mirror;self.leases={}

    def _call(self, operation, page, lease=None, **values):
        return self.request('inventory_v5_worker',page_id=page,
            worker_operation=operation,listing_id=self.identity(page),lease=lease,**values)

    def claim(self,page):
        result=self._call('claim',page)
        lease=result.get('lease')
        if lease:self.leases[page]=lease
        return lease

    def load(self,page,lease):
        row=self._call('load',page,lease)
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
        return self.mirror_port(page,values,deleted=deleted)

    def requeue(self,page,lease,*,reason):
        return self._call('requeue',page,lease,status=reason)

    def renew(self,page,lease):return self._call('renew',page,lease)

    def release(self,page,lease):
        try:return self._call('release',page,lease)
        finally:self.leases.pop(page,None)
