"""Fail-closed reconciliation for uncertain Notion effects.

A lease timeout, HTTP timeout, process death or stable readback cannot prove a
remote request ended. There is no automatic Notion cancellation/status API in
this integration. The production verifier MUST remain unavailable until an
operator has independently established both local-writer quiescence and a
terminal remote outcome (or an upstream drain guarantee for this request).
"""
from dataclasses import dataclass
try:
    from .inventory_v5 import content_hash,field_equal
except ImportError:
    from inventory_v5 import content_hash,field_equal

class RecoveryBlocked(RuntimeError):pass

@dataclass(frozen=True)
class Quiescence:
    writer_reference: str
    remote_reference: str
    request_reference: str
    attestation_id: str


def unavailable_notion_verifier(*args,**kwargs):
    raise RecoveryBlocked('No independent terminal remote-request proof; leave effect barrier in place')


def reconcile_effect(*,repository,notion,page_id,scope,job_id=None,
                     verify_quiescence=unavailable_notion_verifier):
    """Read-only until proof; exact intent CAS gates barrier clearing.

    repository.recovery_snapshot -> {effect,prepared_inputs,pending_patch}
    repository.resolve_effect must atomically compare the exact saved effect
    and reject any changed intent or writer. It cannot claim/replay a patch.
    """
    state=repository.recovery_snapshot(page_id,scope=scope,job_id=job_id)
    effect=state.get('effect')
    if not effect:return {'status':'no_effect'}
    proof=verify_quiescence(effect=effect,page_id=page_id,scope=scope,job_id=job_id)
    if not isinstance(proof,Quiescence) or not all((proof.writer_reference,proof.remote_reference,proof.request_reference,proof.attestation_id)):
        raise RecoveryBlocked('Both writer and exact remote request must be proven terminal')
    intent=effect.get('intent',{})
    if isinstance(intent,str):
        import json
        intent=json.loads(intent)
    patch=intent.get('patch')
    if not isinstance(patch,dict)or not patch:raise RecoveryBlocked('Exact patch intent unavailable')
    current=notion.snapshot(page_id)
    before=state.get('prepared_inputs')
    # A title ticket carries its exact pre-write title rather than a full row.
    if not isinstance(before,dict):raise RecoveryBlocked('Exact pre-effect values unavailable')
    compare_keys=set(before)|set(current) if scope=='worker' else set(before)|set(patch)
    unknown=[k for k in compare_keys if k not in ('_edited_at','_archived') and
             not field_equal(k,current.get(k),before.get(k)) and
             (k not in patch or not field_equal(k,current.get(k),patch[k]))]
    unknown.extend(k for k in patch if k not in current)
    if unknown:raise RecoveryBlocked('Readback has third/new values; owner review required: '+','.join(sorted(set(unknown))))
    remaining={k:v for k,v in patch.items()if not field_equal(k,current.get(k),v)}
    # Reconciliation itself never writes Notion. Resume recognized partial work
    # only in a later freshly leased worker after this barrier is cleared.
    return repository.resolve_effect(page_id,scope=scope,job_id=job_id,
        expected_effect=effect,current=current,remaining=remaining,
        proof={'writer_reference':proof.writer_reference,'remote_reference':proof.remote_reference,
               'request_reference':proof.request_reference,'attestation_id':proof.attestation_id},state_hash=content_hash(state))
