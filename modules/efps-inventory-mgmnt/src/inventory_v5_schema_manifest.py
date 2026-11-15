"""Combined schema/value rehearsal, keyed by stable Notion property IDs.

Plans do not authorize execution. Newly created property IDs must be resolved
and read back before an executable plan can be sealed. SQL mirror state is a
separate surface and requires its own exact before snapshot for rollback.
"""
from copy import deepcopy
try:
    from .inventory_v5 import content_hash
    from .inventory_v5_adapter import serialize_notion
except ImportError:
    from inventory_v5 import content_hash
    from inventory_v5_adapter import serialize_notion


def typed_values(schema, row):
    result={}
    for name,definition in schema.items():
        if definition['type']=='formula':continue
        if name not in row:raise ValueError('Missing exact field value: '+name)
        result[definition['id']]=serialize_notion(row[name],definition['type'])
    return result


def combined_manifest(*,before_schema,before_row,after_schema,after_row,
                      mirror_before=None,mirror_after=None):
    """Full typed post-state plus separate schema, value and mirror operations."""
    for schema in (before_schema,after_schema):
        ids=[v['id'] for v in schema.values()]
        if len(ids)!=len(set(ids)):raise ValueError('Duplicate stable property ID')
    old_title=next((v['id']for v in before_schema.values()if v['type']=='title'),None)
    new_title=next((v['id']for v in after_schema.values()if v['type']=='title'),None)
    if not old_title or old_title!=new_title:raise ValueError('Required title identity must be preserved')
    before={'schema':deepcopy(before_schema),'properties':typed_values(before_schema,before_row),'mirror':deepcopy(mirror_before)}
    after={'schema':deepcopy(after_schema),'properties':typed_values(after_schema,after_row),'mirror':deepcopy(mirror_after)}
    # Title is keyed by its SAME id on both sides. Renaming it never creates a
    # second title property whose inverse would mistakenly clear the old title.
    old_ids={v['id']:name for name,v in before_schema.items()}
    new_ids={v['id']:name for name,v in after_schema.items()}
    forward={key:value for key,value in after['properties'].items()
             if before['properties'].get(key)!=value or
             before_schema.get(old_ids.get(key,''))!=after_schema[new_ids[key]]}
    inverse={key:value for key,value in before['properties'].items()
             if after['properties'].get(key)!=value or
             before_schema[old_ids[key]]!=after_schema.get(new_ids.get(key,''))}
    return {'before':before,'after':after,'before_hash':content_hash(before),'after_hash':content_hash(after),
      'notion':{'schema_before':deepcopy(before_schema),'schema_after':deepcopy(after_schema),
                'typed_patch_by_id':forward,'inverse_typed_patch_by_id':inverse,
                'created_properties':[k for k in new_ids if k not in old_ids]},
      'mirror':{'before':deepcopy(mirror_before),'after':deepcopy(mirror_after),
                'rollback_verified':mirror_before is not None},
      'execution_order':['schema_forward_preserve_ids','typed_value_patch','mirror_patch'],
      'inverse_order':['stop_writers','schema_restore_types_and_names','restore_typed_values_by_id',
                       'restore_mirror_if_before_snapshot_exists','remove_created_properties_after_final_gate'],
      'executable':False,'reason':'Staged rehearsal only; live before snapshots, property-ID readback and approval gate required'}


def apply_combined_model(state,manifest,*,reverse=False):
    """Prove exact whole-state forward/reverse, not a dictionary patch illusion."""
    expected=manifest['after_hash']if reverse else manifest['before_hash']
    if content_hash(state)!=expected:raise ValueError('Schema, row or mirror changed; re-review required')
    if reverse and manifest['after']['mirror'] is not None and manifest['before']['mirror'] is None:
        raise ValueError('Mirror before snapshot unavailable; no exact combined rollback')
    return deepcopy(manifest['before']if reverse else manifest['after'])
