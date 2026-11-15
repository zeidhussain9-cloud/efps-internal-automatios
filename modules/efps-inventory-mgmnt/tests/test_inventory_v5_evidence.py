import pytest
from src.inventory_v5_evidence import evidence_overlay

@pytest.mark.parametrize('raw,b,c',[
 ('Carpet Area:1200 sqft','1290','1200'),
 ('Built-up area:1200 sqft','1200','1110'),
 ('Sqft:1200','1200','1110'),
 ('1200 sqft','1200','1110'),
 ('Carpet area:1200.5 sqft','1290.5','1200.5'),
 ('Built-up area:1400\nCarpet Area:1200','1400','1200')])
def test_area_source_overlay(raw,b,c):
    out,p,issues=evidence_overlay(raw)
    assert not issues
    assert out['built_up_area']==b
    assert out['carpet_area']==c

def test_deposit_month_without_rent_not_an_amount():
    out,p,issues=evidence_overlay('Deposit:6 months')
    assert out['security_deposit']==''
    assert out['monthly_rent']==''
    assert p['security_deposit']['deposit_months']=='6'
    assert issues

def test_rent_alone_never_creates_deposit():
    out,p,issues=evidence_overlay('Rent:40K')
    assert out['monthly_rent']=='40000'
    assert out['security_deposit']==''

def test_months_convert_with_labelled_explicit_rent():
    out,p,issues=evidence_overlay('Rent:40K\nDeposit:6 months')
    assert out['security_deposit']=='240000'
    assert p['security_deposit']['deposit_months']=='6'

def test_lone_currency_is_not_rent():
    out,p,issues=evidence_overlay('Deposit:₹2L')
    assert out['monthly_rent']==''
    assert out['security_deposit']=='200000'

def test_conflicting_rent_is_review_not_first_match():
    out,p,issues=evidence_overlay('Rent:40K\nRent:50K\nDeposit:6 months')
    assert out['monthly_rent']==''
    assert out['security_deposit']==''
    assert issues

def test_balcony_crossline_and_zero_survive_overlay():
    assert evidence_overlay('Rent:40000\nbalcony')[0]['balconies']=='1'
    assert evidence_overlay('No balcony')[0]['balconies']=='0'
