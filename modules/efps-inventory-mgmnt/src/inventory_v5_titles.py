"""Staged title coordinator using real row-state and title-job ports.

No production routing or lifecycle registration. Both durable effect barriers
remain set on uncertain dispatch. Notion read checks are not atomic CAS.
"""
from copy import deepcopy
try:
    from .inventory_v5 import content_hash, field_equal
    from .inventory_v5_repository import V5RenumberRepository
    from .inventory_v5_renumber import run_renumber
except ImportError:
    from inventory_v5 import content_hash, field_equal
    from inventory_v5_repository import V5RenumberRepository
    from inventory_v5_renumber import run_renumber


class TitleBlocked(RuntimeError):
    pass


class CoordinatedTitleRepository(V5RenumberRepository):
    """Holds a row lease from prepare through exact title acknowledgment.

    `notion` must be the sealed/expected-parent V5NotionPort configured with
    this object's bind_dispatch and record_receipt callbacks before running.
    """
    def __init__(self, *, request, workers, notion, schema_loader, sealed_schema_hash):
        super().__init__(request=request, prepare_title=self.prepare,
                         ack_title=self.acknowledge)
        self.workers = workers
        self.notion = notion
        notion.bind_dispatch = self.bind_dispatch
        notion.record_receipt = self.record_receipt
        self.rows = {}
        self.schema_loader = schema_loader
        self.sealed_schema_hash = sealed_schema_hash

    def check_schema(self):
        import re
        if (self.notion.expected_parent or '').replace('-','').lower() != 'bccfd4f55e294b269daa093a928f873a' or not re.fullmatch('[a-f0-9]{64}', self.sealed_schema_hash or ''):
            raise TitleBlocked('Sealed Housing schema and expected parent required')
        schema = self.schema_loader()
        if content_hash(schema) != self.sealed_schema_hash or schema != self.notion.schema or schema.get('SL number', {}).get('type') != 'title':
            raise TitleBlocked('Housing title schema differs from reviewed seal')

    def prepare(self, page, desired, *, before):
        self.check_schema()
        lease = self.workers.claim_title(page)
        if not lease:
            raise TitleBlocked('Dependency row busy or awaiting effect recovery')
        self.rows[page] = {'lease': lease}
        state = self.workers.load(page, lease)
        pending = state.get('pending_patch')
        if pending is not None and (state.get('pending_kind') != 'title' or
                pending != {'SL number': desired} or state.get('prepared_inputs') != before):
            raise TitleBlocked('Pending patch differs from exact resumed title intent')
        acknowledged = state['acknowledged']
        if acknowledged.get('listing_id') != self.workers.identity(page):
            raise TitleBlocked('Reviewed page/listing baseline missing')
        fields = (set(before) | set(acknowledged)) - {'_edited_at', '_archived'}
        changed = [k for k in fields if not field_equal(k, before.get(k), acknowledged.get(k))]
        if changed:
            self.workers.review(page, changed, 'Unacknowledged owner edits before title job')
            raise TitleBlocked('Owner edits require dependency review before title work')
        current = self.notion.snapshot(page)
        if current != before or current.get('_archived'):
            raise TitleBlocked('Page changed before title preparation')
        if pending is None:
            self.workers.prepare_title(page, lease, expected_revision=state['revision'],
                input_values=before, desired=desired)
        self.rows[page].update(before=deepcopy(before), desired=desired)

    def effect(self, job, lease, intent, action):
        page = intent['page_id']
        row = self.rows[page]
        if intent['before'] != {'SL number': row['before'].get('SL number')} or intent['patch'] != {'SL number': row['desired']}:
            raise TitleBlocked('Title intent differs from durable row preparation')
        self.check_schema()
        self.workers.renew(page, row['lease'])
        # A second read after durable preparation catches detected owner races.
        if self.notion.snapshot(page) != row['before']:
            self.workers.review(page, ['SL number'], 'Page changed after title preparation')
            raise TitleBlocked('Page changed after title preparation')
        return super().effect(job, lease, intent,
            lambda: self.workers.effect(page, row['lease'],
                {'kind': 'notion_title', 'patch': intent['patch']}, action))

    def bind_dispatch(self, page, binding):
        self.workers.bind_dispatch(page, binding)
        return super().bind_dispatch(page, binding)

    def record_receipt(self, page, receipt):
        # Save both receipts before the Notion port considers saved-write readback.
        self.workers.record_receipt(page, receipt)
        return super().record_receipt(page, receipt)

    def acknowledge(self, page, desired):
        row = self.rows[page]
        self.check_schema()
        final = self.notion.snapshot(page)
        expected = {**row['before'], 'SL number': desired}
        keys = (set(final) | set(expected)) - {'_edited_at'}
        if desired != row['desired'] or any(not field_equal(k, final.get(k), expected.get(k)) for k in keys):
            self.workers.review(page, ['SL number'], 'Title readback or other page values changed')
            raise TitleBlocked('Title acknowledgment mismatch; pending intent retained')
        self.workers.finish_title(page, row['lease'], final)
        self.workers.release(page, row['lease'])
        self.rows.pop(page)

    def ack_existing_title(self, page, desired):
        # A replay after write/readback but before ack must not skip its durable
        # row intent merely because the visible title already has the rank.
        self.check_schema()
        lease = self.workers.claim_title(page)
        if not lease:
            raise TitleBlocked('Dependency row busy or awaiting effect recovery')
        self.rows[page] = {'lease': lease}
        state = self.workers.load(page, lease)
        final = self.notion.snapshot(page)
        pending = state.get('pending_patch')
        if pending is not None:
            before = state.get('prepared_inputs')
            if state.get('pending_kind') != 'title' or pending != {'SL number': desired} or not isinstance(before, dict):
                raise TitleBlocked('Other pending dependency work must finish first')
            self.rows[page].update(before=before, desired=desired)
            return self.acknowledge(page, desired)
        before = state['acknowledged']
        keys = (set(before) | set(final)) - {'_edited_at'}
        if before.get('listing_id') != self.workers.identity(page) or final.get('SL number') != desired or any(not field_equal(k, final.get(k), before.get(k)) for k in keys):
            self.workers.review(page, ['SL number'], 'Already-numbered page has unacknowledged owner edits')
            raise TitleBlocked('Do not infer generated provenance from matching title')
        self.workers._call('verify_title_mirror',page,lease,values=final)
        self.workers.release(page, lease)
        self.rows.pop(page)

    def close(self):
        for page, row in list(self.rows.items()):
            self.workers.release(page, row['lease'])
            self.rows.pop(page)


def run_coordinated_renumber(*, repository, notion, max_rows=20):
    """Explicit staged entrypoint. Not wired into production/reconciliation."""
    if not isinstance(repository, CoordinatedTitleRepository) or notion is not repository.notion:
        raise TitleBlocked('Durable title coordinator required')
    try:
        return run_renumber(repository=repository, notion=notion, max_rows=max_rows)
    finally:
        repository.close()
