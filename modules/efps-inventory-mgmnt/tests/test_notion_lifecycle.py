from src.notion_lifecycle import finish_processing
from src import notion_intake as intake
import pytest


def canonical_schema():
    s = {name: {'type': kind} for name, kind in intake.listing_property_types().items()}
    for name, values in [('Availability', intake.notion_lifecycle.AVAILABILITY), ('Pipeline Status', intake.notion_lifecycle.PIPELINE), ('WhatsApp Group', ('1 RK / 1–1.5 BHK', '2 / 2.5 BHK', '3 / 3.5 BHK', '4 / 4.5 BHK', '5+ BHK')), ('preferred_tenant_type', ('Family Only', 'Open For All')), ('bachelor_preference', ('Female Only', 'Male Only', 'Not Allowed', 'Open for both'))]:
        s[name]['select'] = {'options': [{'name': n} for n in values]}
    s['live at']['multi_select'] = {'options': [{'name': n} for n in intake.notion_lifecycle.CHANNELS]}
    return s


def test_new_success_and_review_routes():
    assert finish_processing({'status': 'Pending'}) == {'Availability': 'Available', 'Pipeline Status': 'Ready To Post', 'live at': []}
    assert finish_processing({'status': 'Needs Review'})['Pipeline Status'] == 'Needs Review'


@pytest.mark.parametrize('stage', ['Posted', 'Removed'])
def test_success_rerun_preserves_later_stage_channels_availability(stage):
    old = {'Availability': 'On Hold', 'Pipeline Status': stage, 'live at': ['Meta Catalogue', 'Housing.com']}
    assert finish_processing({'status': 'Pending'}, old) == old
    assert finish_processing({'status': 'Needs Review'}, old)['Pipeline Status'] == 'Needs Review'


def test_invalid_existing_canonical_state_never_uses_legacy_fallback():
    with pytest.raises(ValueError):
        finish_processing({'status': 'Pending'}, {'listing_state': 'Available', 'status': 'Pending'})


def test_outgoing_properties_only_new_lifecycle_and_schema_validation():
    row = {'listing_id': 'EF-TEST', 'status': 'Pending', 'intake_status': 'Published', 'listing_state': 'Available', 'meta_catalog_status': 'Posted', 'Availability': 'On Hold', 'Pipeline Status': 'Posted', 'live at': ['Meta Catalogue', 'Housing.com']}
    schema = canonical_schema()
    intake.validate_listing_schema(schema)
    props = intake.listing_notion_properties(row, schema=schema)
    assert not intake.notion_lifecycle.LEGACY_STATUS_FIELDS.intersection(props)
    assert props['Availability'] == {'select': {'name': 'On Hold'}}
    assert props['Pipeline Status'] == {'select': {'name': 'Posted'}}
    assert props['live at'] == {'multi_select': [{'name': 'Meta Catalogue'}, {'name': 'Housing.com'}]}
    intake.validate_listing_properties(schema, props)


def test_snapshot_ignores_disagreeing_old_fields():
    p = {'properties': {'listing_state': {'type': 'select', 'select': {'name': 'Rented Out'}}, 'Availability': {'type': 'select', 'select': {'name': 'Available'}}, 'Pipeline Status': {'type': 'select', 'select': {'name': 'Ready To Post'}}, 'live at': {'type': 'multi_select', 'multi_select': [{'name': 'Housing.com'}]}}}
    snap = intake.listing_snapshot(p)
    assert snap['Availability'] == 'Available'
    assert snap['live at'] == ['Housing.com']
    assert not intake.notion_lifecycle.LEGACY_STATUS_FIELDS.intersection(snap)


@pytest.mark.parametrize('stage', ['Posted', 'Removed', 'Ready To Post'])
def test_raw_rerun_writes_new_lifecycle_and_never_old_columns(monkeypatch, stage):
    def sel(n): return {'type': 'select', 'select': {'name': n}}
    old_props = {'Availability': sel('Rented Out' if stage == 'Removed' else 'Available'), 'Pipeline Status': sel(stage), 'live at': {'type': 'multi_select', 'multi_select': [{'name': 'Housing.com'}]}, 'meta_catalog_id': {'type': 'rich_text', 'rich_text': [{'plain_text': 'existing-product-id'}]}, 'status': sel('Pending'), 'intake_status': sel('Published')}
    class Notion:
        def __init__(self): self.saved=[]; self.updates=[]
        def validate_listing_schema(self): return None
        def find_listing(self, lid): return {'id': 'destination', 'properties': old_props}
        def get_page(self, page_id): return {'parent': {'database_id': intake.INTAKE_DATABASE_ID}, 'properties': {'Raw Property Data': {'rich_text': [{'plain_text': '2 BHK Apartment\nRent: 50000\nLocation: Harlur'}]}, 'Photos': {'files': []}}}
        def update_page(self, page_id, props): self.updates.append(props)
        def save_listing(self, row): self.saved.append(row); return 'destination'
    class Store:
        def claim(self, *args): return 'claimed', {'listing_id': 'EF-2611-AAAA'}
        def finish(self, *args, **kwargs): pass
    def run(raw, *, row, maps_client):
        assert not row.get('meta_catalog_id')
        assert set(row) == set(intake.schema.NAMES)
        row.update(status='Pending',intake_status='Processed',locality='Harlur',BHK='2 BHK',furnish_type='Semi Furnished')
        return row, []
    monkeypatch.setattr(intake.pipeline,'process_closed_session',run)
    n=Notion()
    result=intake.process_page('source',notion=n,store=Store(),cloudinary=object(),maps_client=object())
    assert result['status']=='Processed'
    row=n.saved[0]
    assert row['Pipeline Status']==stage
    assert row['Availability']==('Rented Out' if stage=='Removed' else 'Available')
    assert row['live at']==['Housing.com']
    assert row['meta_catalog_id']=='existing-product-id'
    assert not intake.notion_lifecycle.LEGACY_STATUS_FIELDS.intersection(row)
    assert n.updates[-1]['Intake Status']['status']['name']=='Processed'
