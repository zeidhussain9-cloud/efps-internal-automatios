from copy import deepcopy
import pytest
from src.inventory_v5_schema_manifest import combined_manifest,apply_combined_model

def plan(mirror_before=None):
    old={'Property':{'id':'title','type':'title','title':{}},'flat_furnishings':{'id':'furn','type':'rich_text','rich_text':{}}}
    new={'SL number':{'id':'title','type':'title','title':{}},'flat_furnishings':{'id':'furn','type':'select','select':{'options':[{'name':'Semi Package'}]}},
         'Live On':{'id':'new-live','type':'multi_select','multi_select':{'options':[{'name':'Meta Catalogue'}]}},
         '_SL numeric sort':{'id':'helper','type':'formula','formula':{'expression':'toNumber(prop("SL number"))'}}}
    return combined_manifest(before_schema=old,before_row={'Property':'Old human title','flat_furnishings':'Wardrobe, Fan'},
      after_schema=new,after_row={'SL number':'1','flat_furnishings':'Semi Package','Live On':[]},
      mirror_before=mirror_before,mirror_after={'inventory_contract_version':5,'onboarded_at':'2026-11-15T09:11:00Z'})

def test_combined_title_rename_type_conversion_and_mirror_exact_roundtrip():
    p=plan({'inventory_contract_version':4,'listing_state':'Available'})
    current=apply_combined_model(p['before'],p)
    assert current==p['after']
    assert 'onboarded_at' not in current['properties']
    assert 'inventory_contract_version' not in current['properties']
    assert p['notion']['typed_patch_by_id']['title']['title'][0]['text']['content']=='1'
    assert p['notion']['inverse_typed_patch_by_id']['title']['title'][0]['text']['content']=='Old human title'
    restored=apply_combined_model(current,p,reverse=True)
    assert restored==p['before']
    assert restored['schema']['Property']['id']=='title'
    assert restored['schema']['flat_furnishings']['type']=='rich_text'

def test_newer_row_schema_or_mirror_changes_block_inverse():
    p=plan({'inventory_contract_version':4})
    for key in ('schema','properties','mirror'):
        current=deepcopy(p['after']);current[key]['owner_edit']='new'
        with pytest.raises(ValueError):apply_combined_model(current,p,reverse=True)

def test_missing_mirror_backup_is_not_claimed_reversible():
    p=plan()
    assert not p['mirror']['rollback_verified']
    assert not p['executable']
    with pytest.raises(ValueError,match='Mirror before'):apply_combined_model(p['after'],p,reverse=True)
