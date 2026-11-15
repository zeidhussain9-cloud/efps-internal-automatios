"""Pure migration/rollback guards. No API, SQL, schema or deletion effects."""
from __future__ import annotations
from copy import deepcopy
try:
    from .inventory_v5 import content_hash
except ImportError:
    from inventory_v5 import content_hash
PROTECTED={'listing_id','raw_message_text','cloudinary_image_urls','meta_catalog_id','posted_url','posted_at','google_maps_url','catalog_title'}

def guarded_patch(current,before,patch,*,allowed):
    if content_hash(current)!=content_hash(before):raise ValueError('Row changed since manifest; re-review required')
    if set(patch)-set(allowed):raise ValueError('Patch exceeds reviewed fields')
    if any(k in PROTECTED and patch[k]!=current.get(k)for k in patch):raise ValueError('Protected field mutation')
    return {k:deepcopy(v)for k,v in patch.items()if current.get(k)!=v}

def inverse_patch(current,*,before,applied_patch):
    # Check the full post-migration row, not only changed fields, so rollback
    # cannot silently erase or misrepresent a newer edit elsewhere in the row.
    expected={**before,**applied_patch}
    if content_hash(current)!=content_hash(expected):raise ValueError('Newer edits exist; no automatic rollback')
    return {k:deepcopy(before[k])if k in before else None for k in applied_patch}

def rollback_model(current,*,before,applied_patch):
    inverse_patch(current,before=before,applied_patch=applied_patch)
    # Keys absent before are removed in the model. Real Notion schema rollback
    # is separately ordered before field values and never inferred from this.
    out=deepcopy(current)
    for key in applied_patch:
        if key in before:out[key]=deepcopy(before[key])
        else:out.pop(key,None)
    return out
