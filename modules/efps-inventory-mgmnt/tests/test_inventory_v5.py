"""Pure-rule regressions for the staged contract. No live writes or network."""
import pytest
from src.inventory_v5 import (balcony_evidence, pet_evidence, derive_areas, derive_deposit,
    dependency_patch, channel_array, renumber_plan, text)

@pytest.mark.parametrize('raw,expected',[
    ('No balcony','0'),('without a balcony','0'),('balcony','1'),
    ('Rent:40000\nbalcony','1'),('2 balconies','2'),('Balconies: 0','0'),('', '')])
def test_balcony_line_bound_zero_missing(raw, expected):
    assert balcony_evidence(raw)==(expected,'')

def test_balcony_conflict_does_not_pick_a_value():
    assert balcony_evidence('No balcony\n2 balconies')[0] is None

@pytest.mark.parametrize('raw', ['not pet-friendly','not pet friendly','Pets: No','No pets','Pets not allowed'])
def test_pet_explicit_negatives(raw):
    assert pet_evidence(raw)=='No'

@pytest.mark.parametrize('b,c,exp,want', [
    ('','1200',{'carpet_area'},{'built_up_area':'1290'}),
    ('1200','',{'built_up_area'},{'carpet_area':'1110'}),
    ('1290','1200',{'carpet_area'},{'built_up_area':'1290'}),
    ('1200.5','',{'built_up_area'},{'carpet_area':'1110.5'}),
    ('1300','1190',{'built_up_area','carpet_area'},{}),
    ('1300','1170',set(),{})])
def test_area_provenance_stable_and_decimal(b,c,exp,want):
    assert derive_areas(b,c,exp)==(want,[])

def test_invalid_area_is_review_not_negative():
    assert derive_areas('80','',{'built_up_area'})[1]
    assert derive_areas('','NaN',{'carpet_area'})[1]

def test_deposit_months_with_explicit_rent():
    assert derive_deposit('6','40000')==('240000',[])
    assert derive_deposit('1.5','40000')==('60000',[])
    assert derive_deposit('6','')[0]==''
    assert derive_deposit('6','')[1]

@pytest.mark.parametrize('origin', ['manual','source_explicit','legacy_unknown'])
def test_parent_change_never_overwrites_protected_child(origin):
    out=dependency_patch({'furnish_type':'Fully Furnished','flat_furnishings':'Semi Package'},
       {'furnish_type'},{'flat_furnishings':{'origin':origin}})
    assert out.patch=={}
    assert out.conflicts==('flat_furnishings',)

def test_generated_child_can_update_only_if_still_acknowledged():
    row={'furnish_type':'Fully Furnished','flat_furnishings':'Semi Package'}
    out=dependency_patch(row,{'furnish_type'},{'flat_furnishings':{'origin':'derived','last_generated_value':'Semi Package'}})
    assert out.patch=={'flat_furnishings':'Full Package'}
    out=dependency_patch(row,{'furnish_type'},{'flat_furnishings':{'origin':'derived','last_generated_value':'Other'}})
    assert out.conflicts

def test_empty_manual_is_intentional_and_protected():
    out=dependency_patch({'internal_property_type':'Semi Gated','society_amenities':''},
      {'internal_property_type'},{'society_amenities':{'origin':'manual'}})
    assert 'society_amenities' not in out.patch
    assert 'society_amenities' in out.conflicts

@pytest.mark.parametrize('tenant,gender,want',[
    ('Family Only',None,'-'),('Open For All',None,''),
    ('Open For All','Female Only','Female Only'),('Open For All','Male Only','Male Only')])
def test_settled_tenant_matrix(tenant,gender,want):
    out=dependency_patch({'preferred_tenant_type':tenant},{'preferred_tenant_type'},{},explicit_gender=gender)
    assert out.patch.get('bachelor_preference','')==want

def test_channels_are_arrays_not_joined_text():
    assert channel_array(['Housing.com','Meta Catalogue'])==['Meta Catalogue','Housing.com']
    for bad in ('Meta Catalogue',None,['Unknown'],['Meta Catalogue','Meta Catalogue']):
        with pytest.raises(ValueError):channel_array(bad)

def test_zero_is_not_missing():
    assert text(0)=='0'
    assert text(None)==''

def test_renumber_is_idempotent_newest_first_and_identity_preserving():
    assert renumber_plan(['new','old'],{'old':'1'})==[
      {'page_id':'new','expected_title':'','title':'1'},
      {'page_id':'old','expected_title':'1','title':'2'}]
    assert renumber_plan(['new','old'],{'new':'1','old':'2'})==[]
    with pytest.raises(ValueError):renumber_plan(['same','same'],{})
