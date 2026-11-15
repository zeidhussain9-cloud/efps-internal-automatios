"""Adapter tests never contact a live workspace."""
from datetime import timezone
import pytest
from src.inventory_v5 import content_hash
from src.inventory_v5_adapter import (read_notion_value,serialize_notion,parse_onboarded,
 display_onboarded,migrate_business_values,status_candidate,content_readiness,distribution_allowed)

@pytest.mark.parametrize('value', [[],['Meta Catalogue'],['Meta Catalogue','Housing.com']])
def test_channel_roundtrip_is_typed(value):
    prop={'type':'multi_select',**serialize_notion(value,'multi_select')}
    assert read_notion_value(prop)==value

@pytest.mark.parametrize('value', [0,'0',1,None,''])
def test_numeric_zero_and_null_distinct(value):
    result=serialize_notion(value,'number')
    assert result['number']==(None if value in(None,'')else int(value))

@pytest.mark.parametrize('value', ['-', '', 'Female Only','Male Only'])
def test_select_dash_not_null(value):
    prop={'type':'select',**serialize_notion(value,'select')}
    assert read_notion_value(prop)==value

@pytest.mark.parametrize('iso', ['2026-11-15T09:11:00Z','2026-11-15T14:41:00+05:30'])
def test_dates_preserve_instant_and_display(iso):
    dt=parse_onboarded(iso,legacy_timezone=None)
    shown=display_onboarded(dt,display_timezone='Asia/Calcutta')
    assert shown=='Sunday, November 15, 2026 at 02:41:00 pm'
    back=parse_onboarded(shown,legacy_timezone='Asia/Calcutta')
    assert back.astimezone(timezone.utc)==dt.astimezone(timezone.utc)

def test_legacy_date_requires_zone_and_correct_weekday():
    with pytest.raises(ValueError):parse_onboarded('Sunday, November 15, 2026 at 02:41:00 pm',legacy_timezone=None)
    with pytest.raises(ValueError):parse_onboarded('Monday, November 15, 2026 at 02:41:00 pm',legacy_timezone='Asia/Calcutta')

def test_missing_unknown_boolean_not_false():
    with pytest.raises(ValueError):serialize_notion('', 'checkbox')

def test_readiness_requires_content_not_old_status():
    row={'Availability':'Available','Pipeline Status':'Ready to Post'}
    assert distribution_allowed(row)
    assert content_readiness(row,[],route_valid=True)[0]=='Needs Review'
    for state in('Rented Out','On Hold'):
        assert not distribution_allowed({**row,'Availability':state})

def test_removed_history_needs_approved_identity():
    row={'listing_id':'EF-2609-S75T','listing_state':'Rented Out','meta_catalog_status':'Removed'}
    with pytest.raises(ValueError):status_candidate(row,removed_approved_ids=set())
    assert status_candidate(row,removed_approved_ids={row['listing_id']})=={
      'Availability':'Rented Out','Pipeline Status':'Removed','Live On':[]}

def test_full109_snapshot_candidate_mapping_is_independent_of_network():
    # The source-controlled fixture is deliberately synthetic, no private listing dump.
    row={'listing_id':'EF-2609-DS5K','furnish_type':'Semi Furnished',
      'flat_furnishings':'Wardrobe, Modular Kitchen, Geyser, Fan, Light',
      'internal_property_type':'Semi Gated',
      'society_amenities':'Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area',
      'preferred_tenant_type':'Open For All','bachelor_preference':'Open for both','BHK':'1 RK'}
    with pytest.raises(ValueError):migrate_business_values(row)
    correction={'before_hash':content_hash(row),'patch':{'society_amenities':'Standard Amenities'}}
    correction['after_hash']=content_hash({**row,**correction['patch']})
    out=migrate_business_values(row,reviewed_correction=correction)
    assert out['flat_furnishings']=='Semi Package'
    assert out['society_amenities']=='Standard Amenities'
    assert out['bachelor_preference']==''
    assert row['bachelor_preference']=='Open for both'  # no input mutation
    with pytest.raises(ValueError):migrate_business_values({**row,'BHK':'6 BHK'})

@pytest.mark.parametrize('bad',['2026-11-15','2026-11-15T09:11:00','2026-02-31T09:11:00Z'])
def test_unqualified_or_invalid_iso_is_not_assigned_a_zone(bad):
    with pytest.raises(ValueError):parse_onboarded(bad,legacy_timezone='Asia/Calcutta')


def test_reviewed_case_is_hash_bound_not_permanent_id_permission():
    row={'listing_id':'EF-2609-GJY7','furnish_type':'Semi Furnished','flat_furnishings':'Semi Package',
      'internal_property_type':'Semi Gated','society_amenities':'Standard Amenities',
      'preferred_tenant_type':'Family','bachelor_preference':'Female Only','BHK':'2 BHK'}
    with pytest.raises(ValueError):migrate_business_values(row)
    fix={'before_hash':content_hash(row),'patch':{'preferred_tenant_type':'Open For All','bachelor_preference':'Female Only'}}
    fix['after_hash']=content_hash({**row,**fix['patch']})
    assert migrate_business_values(row,reviewed_correction=fix)['preferred_tenant_type']=='Open For All'
    with pytest.raises(ValueError):migrate_business_values({**row,'bachelor_preference':'Male Only'},reviewed_correction=fix)
    # The same ID with a later settled owner choice is not forced to the old answer.
    later={**row,'preferred_tenant_type':'Open For All','bachelor_preference':'Male Only'}
    assert migrate_business_values(later)['bachelor_preference']=='Male Only'


def test_rich_text_inverse_preserves_source_whitespace_exactly():
    for kind in ('title','rich_text'):
        exact='  Original source  \n'
        assert read_notion_value({'type':kind,**serialize_notion(exact,kind)})==exact


def test_long_rich_text_is_losslessly_chunked_for_notion_limit():
    value='  '+('x'*2489)+'\n'+('y'*2100)+'  '
    typed=serialize_notion(value,'rich_text')
    assert all(len(part['text']['content'])<=2000 for part in typed['rich_text'])
    assert read_notion_value({'type':'rich_text',**typed})==value


@pytest.mark.parametrize('kind',['rich_text','title'])
def test_rich_text_array_limit_and_astral_chunks_fail_closed(kind):
    value='😀'*1001
    parts=serialize_notion(value,kind)[kind]
    assert [len(p['text']['content']) for p in parts]==[1000,1]
    assert ''.join(p['text']['content']for p in parts)==value
    with pytest.raises(ValueError,match='100 elements'):
        serialize_notion('x'*200001,kind)


def test_total_properties_payload_limit_precedes_binding_and_http():
    from src.inventory_v5_notion import V5NotionPort
    seen=[]
    class Client:
        def update_page(self,*args):seen.append('http')
    schema={name:{'type':'rich_text'}for name in ['a','b','c']}
    port=V5NotionPort(Client(),schema,bind_dispatch=lambda *args:seen.append('bind'))
    with pytest.raises(ValueError,match='500KB'):
        port.patch('test',{name:'x'*180000 for name in schema})
    assert seen==[]
