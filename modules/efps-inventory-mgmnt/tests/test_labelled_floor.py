"""Single labelled floors from the existing formatted intake workflow."""
from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import extract
import pipeline
from notion_intake import build_whatsapp_post


@pytest.mark.parametrize('line,expected', [('Floor: 3rd','3'), ('Floor: 1st','1'), ('Floor: 2nd','2'), ('Floor: 11th','11'), ('FLOOR - 3RD','3'), ('Floor: 3','3'), ('Floor: 03rd','3')])
def test_single_labelled_floor_without_inventing_total(line, expected):
    row = extract.scan(line)
    assert row['floor_number'] == expected
    assert not row.get('total_floors')


@pytest.mark.parametrize('line', ['Floor: 3rd or 4th', 'Floor: 3-4', 'Floor: All Floors', 'Floor: 3rd?', 'Floor: approximately 3rd', 'Floor: not 3rd', 'Floor: 3rd/unknown', 'Floor: 3.5', 'Floor: 300', 'Floor: 3rd\nFloor: 4th'])
def test_ambiguous_or_invalid_labelled_values_not_truncated(line):
    assert not extract.scan(line).get('floor_number')


def test_existing_combined_and_prose_floor_paths_preserved():
    row = extract.scan('Floor: 7/9')
    assert row['floor_number'] == '7' and row['total_floors'] == '9'
    assert extract.scan('3rd floor')['floor_number'] == '3'


def test_park_vista_formatted_shape_carries_floor_into_caption():
    raw = ('Fully Furnished 2 BHK with 2 Bathrooms, 1 Balcony & Utility\n'
           'Rent: 60K\nMaintenance: 5K\nDeposit: 2L\nSqft: 1219\nFloor: 3rd\n'
           'Available from: Ready to Occupy\nPreferred tenant: Open For All\nPets: Allowed\n'
           'Gated Community\nLocation: Haralur\nSociety: SJR Park Vista\n')
    row = pipeline.deterministic(raw, row=pipeline.initial_row('EF-TEST-FLOOR', raw))
    assert row['floor_number'] == '3'
    assert row['total_floors'] == ''
    assert '📐 1219 sqft | Floor 3' in build_whatsapp_post(row, raw, maps_verified=False, allow_unverified_source_map=True)
