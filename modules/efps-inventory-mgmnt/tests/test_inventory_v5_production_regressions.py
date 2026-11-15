"""Regressions on the existing production functions, not only new pure helpers."""
import pytest
from src import extract,normalize,notion_intake

@pytest.mark.parametrize('raw,value', [('No balcony','0'),('Rent:40000\nbalcony','1')])
def test_scan_then_normalize_balcony_chain(raw,value):
    row=normalize.normalize(extract.scan(raw),raw)
    assert row['balconies']==value
    assert notion_intake.listing_notion_properties(row)['balconies']['number']==int(value)

def test_scan_carpet_only_does_not_also_create_built_up():
    assert extract.scan('Carpet area:1200 sqft')['carpet_area']=='1200'
    assert 'built_up_area' not in extract.scan('Carpet area:1200 sqft')

def test_no_rent_months_retained_as_unit_not_amount():
    assert extract.scan('Deposit:6 months')['security_deposit']=='6 months'

def test_numeric_zero_not_lost_by_normalizer_or_text_writer():
    assert normalize.normalize({'balconies':0},'')['balconies']=='0'
    assert notion_intake._serialize_text_field(0,'rich_text','test')['rich_text'][0]['text']['content']=='0'

@pytest.mark.parametrize('raw',['not pet-friendly','not pet friendly','Pets: No'])
def test_pet_field_and_caption_policy_agree(raw):
    assert normalize.normalize({},raw)['pet_friendly']=='No'
    assert notion_intake._explicit_pet_policy(raw)=='Not Allowed'

def test_measurement_area_label_not_used_as_locality():
    assert not extract.scan('Area:1200 sqft').get('locality')
    assert extract.scan('Area:Haralur')['locality']=='Haralur'
