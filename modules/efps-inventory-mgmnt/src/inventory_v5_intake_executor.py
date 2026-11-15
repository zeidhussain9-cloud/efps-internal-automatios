"""Staged existing-destination executor; never creates pages or completes sources.

Uses actual row effect/receipt/mirror ports and a durable source phase ledger.
Importing this module does not alter intake routing, extraction, media or posting.
"""
from copy import deepcopy
try:
    from .inventory_v5 import content_hash, field_equal
    from .inventory_v5_intake import (destination_candidate,existing_destination_plan,
        validate_destination_schema,IntakeDestinationBlocked,PARENT)
except ImportError:
    from inventory_v5 import content_hash, field_equal
    from inventory_v5_intake import (destination_candidate,existing_destination_plan,
        validate_destination_schema,IntakeDestinationBlocked,PARENT)


class SubmissionRepository:
    def __init__(self,request):self.request=request
    def call(self,operation,source,lease=None,**values):
        return self.request('inventory_v5_intake_submission',worker_operation=operation,
            source_page_id=source,lease=lease,**values)


def _same(left,right):
    return all(field_equal(k,left.get(k),right.get(k))for k in (set(left)|set(right))-{'_edited_at'})


def save_existing_destination(*,source_page_id,payload_hash,page_id,processed,
        workers,submissions,notion,schema_loader,sealed_schema_hash,verify_binding):
    """Prepare/readback/mirror/ack an existing known destination, source stays pending.

    verify_binding must resolve the durable existing source/listing/page mapping
    and reject multiple matches; no page identity is inferred from candidate data.
    No durable-ledger phase authorizes a source success or a new create.
    """
    listing_id=processed.get('listing_id')
    def validate():
        schema=schema_loader()
        validate_destination_schema(schema,sealed_schema_hash=sealed_schema_hash)
        if schema!=notion.schema or (notion.expected_parent or '').replace('-','').lower()!=PARENT:
            raise IntakeDestinationBlocked('Sealed canonical Housing port required')
        binding=verify_binding(source_page_id,listing_id,page_id)
        if binding!={'source_page_id':source_page_id,'listing_id':listing_id,'page_id':page_id,'active':True,'unique':True}:
            raise IntakeDestinationBlocked('Exact unique active source/listing/page binding required')
        return schema
    schema=validate()
    candidate=destination_candidate(processed,schema=schema,sealed_schema_hash=sealed_schema_hash)
    submission=submissions.call('claim',source_page_id,page_id=page_id,
        payload_hash=payload_hash,listing_id=listing_id,candidate=candidate)
    if submission.get('busy'):return {'status':'busy','source_completion_allowed':False}
    source_lease=submission['lease_token'];row_lease=None
    marker={'source_page_id':source_page_id,'payload_hash':payload_hash}
    # Dedicated callbacks retain exact dispatch and terminal evidence for a row.
    notion.bind_dispatch=workers.bind_dispatch;notion.record_receipt=workers.record_receipt
    def renew():
        submissions.call('renew',source_page_id,source_lease)
        workers.renew(page_id,row_lease)
    try:
        claim=workers._claim(page_id,'claim_intake')
        if not claim:return {'status':'busy','source_completion_allowed':False}
        row_lease=claim
        state=workers.load(page_id,row_lease)
        if state['acknowledged'].get('listing_id')!=listing_id or workers.identity(page_id)!=listing_id:
            raise IntakeDestinationBlocked('Reviewed destination baseline/identity required')
        current=notion.snapshot(page_id)
        if current.get('_archived'):raise IntakeDestinationBlocked('Destination lifecycle handling required')
        plan=submission.get('plan')
        if plan is None:
            if state.get('pending_patch') is not None:raise IntakeDestinationBlocked('Other pending row work must finish')
            plan=existing_destination_plan(candidate=candidate,current=current,
                acknowledged=state['acknowledged'],provenance=state['provenance'],listing_id=listing_id)
            plan['revision']=state['revision']
            submissions.call('plan',source_page_id,source_lease,plan=plan)
        before=plan['before'];patch=plan['patch'];expected={**before,**patch}
        if current.get('listing_id')!=listing_id:
            raise IntakeDestinationBlocked('Destination listing identity changed')
        pending=state.get('pending_patch')
        prepared=state.get('prepared_inputs')
        if pending is not None:
            if state['revision'] != plan['revision']:
                raise IntakeDestinationBlocked('Frozen pending destination revision changed; explicit resolution required')
            if state.get('pending_kind')!='intake' or state.get('pending_submission')!=marker or pending!=patch or prepared!=before:
                raise IntakeDestinationBlocked('Different pending destination intent')
            if any(not field_equal(k,current.get(k),before.get(k)) and not field_equal(k,current.get(k),expected.get(k))
                   for k in (set(before)|set(current)) - {'_edited_at'}):
                workers.review(page_id,list(patch),'Interrupted destination conflicts with owner edits')
                raise IntakeDestinationBlocked('New owner values prevent intake replay')
        elif submission.get('plan') is not None and state['revision']==plan['revision']+1 and _same(state['acknowledged'],expected) and _same(current,expected):
            # Crash after row ack but before source-ledger ack. Do not reapply.
            submissions.call('destination_ack',source_page_id,source_lease)
            return {'status':'awaiting_source_ack','conflicts':plan['conflicts'],'source_completion_allowed':False}
        else:
            # A durable source plan freezes the destination revision too. Even
            # an unchanged-value worker/title/other-source acknowledgment may
            # advance it. Do not mutate against a stale plan and strand its ack.
            if state['revision'] != plan['revision']:
                raise IntakeDestinationBlocked('Frozen destination revision changed; explicit blocked-plan resolution required before writes')
            if not _same(current,before) or not _same(state['acknowledged'],before):
                raise IntakeDestinationBlocked('Destination changed since durable source plan')
            workers._call('prepare_intake',page_id,row_lease,revision=state['revision'],
                values=before,patch=patch,provenance=plan['provenance'],review=marker)
        validate();renew()
        check=notion.snapshot(page_id)
        if check!=current:raise IntakeDestinationBlocked('Concurrent edit before destination write')
        remaining={k:v for k,v in patch.items()if not field_equal(k,current.get(k),v)}
        if remaining:
            workers.effect(page_id,row_lease,{'kind':'intake_destination','patch':remaining,'submission':marker},
                lambda:notion.patch(page_id,remaining))
        validate();renew()
        final=notion.snapshot(page_id)
        if not _same(final,expected):
            workers.review(page_id,list(patch),'Destination readback conflicts with owner values')
            raise IntakeDestinationBlocked('Destination readback mismatch')
        # This port is lease/revision-qualified actual Edge/SQL mirror, not a
        # blind legacy save. Completion cannot precede a successful mirror.
        workers.mirror(page_id,final,deleted=False)
        validate();renew()
        after_mirror=notion.snapshot(page_id)
        if after_mirror!=final:
            workers.review(page_id,list(patch),'Owner edit after destination mirror; retain pending acknowledgment')
            raise IntakeDestinationBlocked('Destination changed after mirror')
        workers._call('finish_intake',page_id,row_lease,values=final,review=marker)
        submissions.call('destination_ack',source_page_id,source_lease)
        return {'status':'awaiting_source_ack','conflicts':plan['conflicts'],'source_completion_allowed':False}
    finally:
        try:
            if row_lease:workers.release(page_id,row_lease)
        finally:submissions.call('release',source_page_id,source_lease)
