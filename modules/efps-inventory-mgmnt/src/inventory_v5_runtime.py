"""Disabled-by-default existing-Housing runtime adapter, never Raw Intake.

Deployment, schema sealing, seeded state and membership/title orchestration are
separate gates. No fallback to an old writer after a v5 failure is allowed.
"""
from __future__ import annotations
import re
try:
    from .inventory_v5 import content_hash
    from .inventory_v5_adapter import parse_onboarded
    from .inventory_v5_http import V5HttpNotionClient
    from .inventory_v5_notion import V5NotionPort
    from .inventory_v5_repository import V5Repository
    from .inventory_v5_worker import process_dependencies
except ImportError:
    from inventory_v5 import content_hash
    from inventory_v5_adapter import parse_onboarded
    from inventory_v5_http import V5HttpNotionClient
    from inventory_v5_notion import V5NotionPort
    from inventory_v5_repository import V5Repository
    from inventory_v5_worker import process_dependencies


class RuntimeBlocked(RuntimeError):
    pass


class SeededRepository(V5Repository):
    def load(self, page, lease):
        state = super().load(page, lease)
        if state['acknowledged'].get('listing_id') != self.identity(page):
            raise RuntimeBlocked('Reviewed v5 baseline/identity seed is required; no bootstrap from a live edit')
        return state


def process_existing_housing(page_id, *, client, store, schema, sealed_schema_hash,
                             render_caption, route_bhk):
    """Use real dependency ports for an already seeded, active Housing page.

    Explicitly refuses missing identity/schema seed, deletion/restoration and
    new membership. Title jobs/reconciler need their own coordinated adapter.
    """
    if not re.fullmatch(r'[a-f0-9]{64}', sealed_schema_hash or ''):
        raise RuntimeBlocked('Reviewed production schema seal is missing')
    if content_hash(schema) != sealed_schema_hash:
        raise RuntimeBlocked('Housing schema changed since the reviewed seal')
    required = {'SL number': 'title', 'Availability': 'select',
                'Pipeline Status': 'select', 'Live On': 'multi_select',
                '_SL numeric sort': 'formula'}
    if any(schema.get(name, {}).get('type') != kind for name, kind in required.items()):
        raise RuntimeBlocked('Housing v5 schema is incomplete')
    known = store.find_inventory(page_id)
    identity = str(known.get('listing_id') or '')
    if not known.get('found') or not re.fullmatch(r'EF-\d{4}-[0123456789ABCDEFGHJKMNPQRSTVWXYZ]{4}', identity):
        raise RuntimeBlocked('New Housing membership requires reviewed identity/order registration')
    if known.get('deleted_at'):
        raise RuntimeBlocked('Housing restoration requires coordinated membership/title handling')

    def mirror(page, values, *, deleted, lease, revision):
        if deleted:
            raise RuntimeBlocked('Housing deletion requires coordinated membership/title handling')
        row = {k: v for k, v in values.items() if not k.startswith('_')}
        # Invalid historical dates block projection rather than gaining a guessed instant.
        instant = parse_onboarded(row.get('onboarded_on'), legacy_timezone='Asia/Calcutta')
        row.update(inventory_contract_version=5, onboarded_at=instant.isoformat())
        return store._request('sync_inventory', page_id=page, listing_id=identity,
                              row=row, deleted=False, lease=lease, revision=revision,
                              source_hash=content_hash(row))

    repo = SeededRepository(request=store._request, identity=lambda page: identity, mirror=mirror)
    http = V5HttpNotionClient(token=client.token, version='2022-06-28', session=client.session)
    notion = V5NotionPort(http, schema, bind_dispatch=repo.bind_dispatch, record_receipt=repo.record_receipt)
    # A known archived page must not enter the legacy mirror or mutate membership.
    initial = notion.snapshot(page_id)
    if initial.get('_archived'):
        raise RuntimeBlocked('Housing deletion requires coordinated membership/title handling')
    result = process_dependencies(page_id, notion=notion, repository=repo,
                                  render_caption=render_caption, route_bhk=route_bhk)
    return {**result, 'inventory_contract_version': 5, 'listing_id': identity}
