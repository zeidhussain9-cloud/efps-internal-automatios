from __future__ import annotations
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import extract
import pipeline
from location_match import normalize_locality
from notion_intake import build_whatsapp_post

RAW = ('SJR Pavillion, Bellandur, Gated Community, 3BHK, 3 Bathrooms, '
       '2 Balconies, utility, per friendly, open for all, Available from 1st December, '
       'Rent : 85k, 6-7K Aprox is the maintenance, \n\n'
       'https://maps.app.goo.gl/oMaQfeb3An1MucrBA\n')


def test_exact_real_submission_extracts_names_without_changing_raw_or_defaults():
    row = pipeline.deterministic(RAW, row=pipeline.initial_row('EF-2611-5519', RAW))
    assert row['locality'] == 'Bellandur'
    assert row['society_name'] == 'SJR Pavillion'
    assert row['raw_message_text'] == RAW.strip()  # Existing normalization trims outer whitespace.
    assert row['monthly_rent'] == '85000'
    assert row['covered_parking'] == '1'  # Existing default, not changed by this fix.
    assert row['society_amenities'].startswith('Club House,')
    result = normalize_locality(row['locality'], ['Haralur', 'Bellandur'])
    assert result.canonical == 'Bellandur'
    caption = build_whatsapp_post(row, RAW, maps_verified=False, allow_unverified_source_map=True)
    assert 'Location: *Bellandur*' in caption
    assert 'Original Maps link (not verified)' in caption
    assert 'https://maps.app.goo.gl/oMaQfeb3An1MucrBA' in caption


@pytest.mark.parametrize('raw, expected', [
    ('SJR Pavillion, bellandur, gated community, 3BHK', {'society_name':'SJR Pavillion','locality':'bellandur'}),
    ('Bellandur, Standalone, 2 BHK', {'locality':'Bellandur'}),
    ('Example Residency, Harlur, Semi Gated, 2 BHK', {'society_name':'Example Residency','locality':'Harlur'}),
])
def test_bounded_property_headers(raw, expected):
    assert extract.prose_location(raw) == expected


@pytest.mark.parametrize('raw', [
    'SJR Pavillion, Bellandur, 3 BHK',  # No property-type header anchor.
    'Rent 85000, Bellandur, Gated Community',
    'SJR Pavillion, Bellandur or Haralur, Gated Community',
    'SJR Pavillion, not Bellandur, Gated Community',
    'SJR Pavillion, near Bellandur, Gated Community',
    'Society: SJR Pavillion, Bellandur, Gated Community',
    'SJR Pavillion, Bellandur, Haralur, Gated Community',
    'Looking for, Bellandur, Gated Community',
    'SJR Pavillion, 3 BHK, Gated Community',
])
def test_ambiguous_headers_do_not_invent_locations(raw):
    assert extract.prose_location(raw) == {}


def test_explicit_fields_override_comma_header():
    row = extract.scan('SJR Pavillion, Bellandur, Gated Community\nLocation: Haralur\nSociety: Explicit Name')
    assert row['locality'] == 'Haralur'
    assert row['society_name'] == 'Explicit Name'


def test_unknown_prose_locality_still_requires_review_by_normalizer():
    candidate = extract.prose_location('Example Residency, Timbuktu, Gated Community')['locality']
    assert normalize_locality(candidate, ['Haralur', 'Bellandur']).canonical == ''


def test_full_intake_exact_submission_maps_outage_reuses_listing(monkeypatch):
    from src import notion_intake as intake
    from types import SimpleNamespace
    monkeypatch.delenv('EFPS_AI_REVIEW_ENABLED', raising=False)
    monkeypatch.delenv('EFPS_AI_BEAUTIFY_ENABLED', raising=False)
    class Notion:
        _listing_schema = {'locality': {'type':'select', 'select':{'options':[{'name':'Bellandur'}]}}}
        saved = None
        final = None
        def get_page(self, page_id):
            return {'parent':{'database_id':intake.INTAKE_DATABASE_ID}, 'created_time':'2026-11-15T08:12:00Z',
                    'properties':{'Raw Property Data':{'rich_text':[{'plain_text':RAW}]},'Photos':{'files':[]}}}
        def validate_listing_schema(self): return self._listing_schema
        def update_page(self, page_id, props): self.final = props
        def find_listing(self, listing_id): return None
        def save_listing(self, row): self.saved = row; return 'existing-housing-id'
    class Store:
        def claim(self, page_id, payload_hash): return 'claimed', {'listing_id':'EF-2611-5519'}
        def finish(self, page_id, state, **kwargs): self.state = state
    class Maps:
        def resolve(self, **kwargs): return SimpleNamespace(confidence='API_UNAVAILABLE')
    class Ola:
        def geocode(self, text): raise AssertionError('Exact canonical locality needs no geocoding')
    notion, store = Notion(), Store()
    result = intake.process_page('test-page', notion=notion, store=store, cloudinary=object(), maps_client=Maps(), ola_client=Ola())
    assert result['status'] == 'Processed'
    assert result['listing_id'] == 'EF-2611-5519'
    assert notion.saved['locality'] == 'Bellandur'
    assert notion.saved['society_name'] == 'SJR Pavillion'
    assert 'Location: *Bellandur*' in notion.saved['whatsapp_post']
    assert notion.final['Processed Property']['relation'] == [{'id':'existing-housing-id'}]
    assert store.state == 'processed'
