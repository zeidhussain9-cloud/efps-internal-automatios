"""Staged dependency worker. All effects are explicit injected ports.

Not wired into the live webhook until SQL, adapter and conflict gates pass.
"""
from __future__ import annotations
from dataclasses import asdict
try:
    from .inventory_v5 import dependency_patch, content_hash, field_equal
except ImportError:
    from inventory_v5 import dependency_patch, content_hash, field_equal

IMMUTABLE = {'listing_id', 'onboarded_on', 'raw_message_text', 'cloudinary_image_urls',
             'meta_catalog_id', 'meta_catalog_status', 'posted_url', 'posted_at', 'Live On'}
TITLE_FIELDS = {'Property', 'SL number'}


def semantic_changes(before, after):
    return {k for k in set(before) | set(after) if not field_equal(k,before.get(k),after.get(k))}


def process_dependencies(page_id, *, notion, repository, render_caption, route_bhk):
    """Lease -> diff -> protect -> derive -> recheck -> narrow patch -> readback.

    The repository must implement durable per-listing CAS/lease semantics and
    pending-write recovery. A Notion read-then-write still is not atomic against
    human edits. Post-write conflicts are surfaced, never certified impossible.
    """
    lease = repository.claim(page_id)
    if not lease:
        if getattr(repository,'blocked_state',{}).get(page_id,{}).get('needs_recovery'):
            return {'status':'needs_recovery','blocked':True,'reason':'Uncertain external write; manual incident review required'}
        return {'status': 'busy'}
    try:
        state = repository.load(page_id, lease)
        current = notion.snapshot(page_id)
        if current.get('_archived'):
            repository.mirror(page_id, current, deleted=True)
            repository.finish(page_id, lease, current, status='deleted')
            return {'status': 'deleted'}
        before = state['acknowledged']
        pending = state.get('pending_patch')
        prepared = state.get('prepared_inputs')
        if pending is not None and prepared is not None:
            # Replay only an exactly recognized partial self-write. A third
            # value, including an unrelated human edit, stops automatic replay.
            unknown = [k for k in set(prepared) | set(current)
                       if k != '_edited_at' and not field_equal(k,current.get(k),prepared.get(k))
                       and (k not in pending or not field_equal(k,current.get(k),pending[k]))]
            if unknown:
                repository.review(page_id, unknown, 'Interrupted write conflicts with newer values; no replay')
                repository.requeue(page_id, lease, reason='recovery_conflict')
                return {'status': 'needs_review', 'conflicts': sorted(unknown)}
            repository.renew(page_id, lease)
            check = notion.snapshot(page_id)
            if check != current:
                repository.requeue(page_id, lease, reason='recovery_concurrent_edit')
                return {'status': 'retry', 'reason': 'concurrent_edit'}
            remaining = {k:v for k,v in pending.items() if not field_equal(k,current.get(k),v)}
            if remaining:repository.effect(page_id,lease,{'kind':'notion_patch','patch':remaining},lambda:notion.patch(page_id,remaining))
            final = notion.snapshot(page_id)
            if any(not field_equal(k,final.get(k),v) for k,v in pending.items()):
                repository.review(page_id, list(pending), 'Interrupted-write replay readback mismatch')
                repository.requeue(page_id, lease, reason='recovery_readback_conflict')
                return {'status': 'retry', 'reason': 'post_write_conflict'}
            if state['acknowledged'].get('listing_id') in (None,final.get('listing_id')):
                repository.mirror(page_id, final, deleted=False)
            else:repository.quarantine_identity(page_id,lease)
            repository.finish(page_id, lease, final, status='recovered')
            return {'status': 'recovered', 'changed': sorted(remaining)}
        provenance = {k: dict(v) for k, v in state.get('provenance', {}).items()}
        changed = semantic_changes(before, current) - {'_edited_at', '_archived'}
        expected = state.get('expected_self_write') or {}
        # Suppress exactly acknowledged generated values, not all events nearby.
        external = {k for k in changed if k not in expected or not field_equal(k,current.get(k),expected[k])}
        if not external:
            repository.mirror(page_id, current, deleted=False)
            repository.finish(page_id, lease, current, status='self_write_acknowledged')
            return {'status': 'self_write_acknowledged'}
        for field in external - TITLE_FIELDS:
            provenance[field] = {'origin': 'manual', 'revision': state['revision'] + 1}
        if external & IMMUTABLE:
            protected=sorted(external & IMMUTABLE)
            repository.review(page_id, protected, 'Protected identity/source/downstream fields changed')
            repository.renew(page_id,lease)
            check=notion.snapshot(page_id)
            if check!=current:
                repository.requeue(page_id,lease,reason='protected_change_race')
                return {'status':'retry','reason':'concurrent_edit'}
            safety_patch={'Pipeline Status':'Needs Review'}
            repository.prepare(page_id,lease,expected_revision=state['revision'],input_hash=content_hash(current),
                input_values=current,patch=safety_patch,provenance=provenance)
            repository.effect(page_id,lease,{'kind':'notion_patch','patch':safety_patch},lambda:notion.patch(page_id,safety_patch))
            final=notion.snapshot(page_id)
            if final.get('Pipeline Status')!='Needs Review':
                repository.requeue(page_id,lease,reason='protected_status_readback')
                return {'status':'retry','reason':'post_write_conflict'}
            # An edited identity cannot be mirrored under a guessed identity.
            if 'listing_id' not in protected:repository.mirror(page_id, final, deleted=False)
            else:repository.quarantine_identity(page_id,lease)
            repository.finish(page_id, lease, final, status='needs_review')
            return {'status': 'needs_review', 'protected': protected}
        evidence = state.get('source_evidence') or {}
        result = dependency_patch(current, external - TITLE_FIELDS, provenance,
              deposit_months=evidence.get('deposit_months'), explicit_gender=evidence.get('explicit_gender'))
        patch = dict(result.patch)
        issues = list(result.issues)
        conflicts = list(result.conflicts)
        if 'BHK' in external:
            group, destination = route_bhk(current.get('BHK', ''))
            if group and destination and not any('Unsupported BHK' in x for x in issues):
                for field, value in [('WhatsApp Group', group), ('WhatsApp Destination', destination)]:
                    old = provenance.get(field, {})
                    if old.get('origin','legacy_unknown') in ('manual', 'legacy_unknown', 'source_explicit') and current.get(field) != value:
                        conflicts.append(field)
                    else:
                        patch[field] = value
            else:
                # Routing is not deleted when manual. Eligibility is disabled.
                issues.append('Distribution disabled until valid BHK routing is restored')
        # Title-only renumber writes must never regenerate a caption.
        caption_inputs = external - TITLE_FIELDS - {'Availability', 'Pipeline Status'}
        if caption_inputs or patch:
            caption = render_caption({**current, **patch})
            old = provenance.get('whatsapp_post', {})
            if current.get('whatsapp_post') != caption:
                if old.get('origin') == 'derived' and old.get('last_generated_value') == current.get('whatsapp_post'):
                    patch['whatsapp_post'] = caption
                else:
                    conflicts.append('whatsapp_post')
        # Review is recorded separately so an error handler cannot wipe old notes.
        if conflicts or issues:
            repository.review(page_id, sorted(set(conflicts)), '; '.join(issues) or 'Manual dependent field conflicts with parent')
            patch['Pipeline Status'] = 'Needs Review'
        repository.renew(page_id, lease)
        inputs = set(current) - {'_edited_at'}
        refetched = notion.snapshot(page_id)
        if any(refetched.get(k) != current.get(k) for k in inputs | set(refetched)):
            repository.requeue(page_id, lease, reason='concurrent_edit_before_patch')
            return {'status': 'retry', 'reason': 'concurrent_edit'}
        # Store intent before effect. If the process crashes after patch, a retry
        # compares exact resulting fields and resumes rather than double-deriving.
        for field, value in patch.items():
            provenance[field] = {**provenance.get(field, {}), 'origin':'derived', 'last_generated_value':value,
                                 'derivation_version':5, 'revision':state['revision']+1}
        repository.prepare(page_id, lease, expected_revision=state['revision'],
             input_hash=content_hash(current), input_values=current, patch=patch, provenance=provenance)
        repository.renew(page_id, lease)
        if patch:
            repository.effect(page_id,lease,{'kind':'notion_patch','patch':patch},lambda:notion.patch(page_id,patch))
        final = notion.snapshot(page_id)
        mismatches = [k for k, v in patch.items() if not field_equal(k,final.get(k),v)]
        if mismatches:
            repository.review(page_id, mismatches, 'Concurrent edit or partial write after dependency patch')
            repository.requeue(page_id, lease, reason='post_write_conflict')
            return {'status': 'retry', 'reason': 'post_write_conflict'}
        repository.mirror(page_id, final, deleted=False)
        repository.finish(page_id, lease, final, status='needs_review' if conflicts or issues else 'recalculated')
        return {'status': 'needs_review' if conflicts or issues else 'recalculated', 'changed': sorted(patch), 'conflicts': sorted(set(conflicts)), 'issues': issues}
    finally:
        repository.release(page_id, lease)
