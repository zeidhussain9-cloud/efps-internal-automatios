import pytest
from src.inventory_v5_migration import guarded_patch,inverse_patch,rollback_model

def test_exact_reviewed_patch_and_inverse_restore_model():
    before={'listing_id':'EF-2611-ABCD','x':'old','photo':'keep'};patch={'x':'new','new_field':[]}
    applied=guarded_patch(before,before,patch,allowed={'x','new_field'})
    current={**before,**applied};assert inverse_patch(current,before=before,applied_patch=applied)=={'x':'old','new_field':None}
    assert rollback_model(current,before=before,applied_patch=applied)==before

def test_changed_source_or_newer_user_edit_prevents_write_and_rollback():
    before={'listing_id':'EF-2611-ABCD','x':'old','other':'old'};patch={'x':'new'}
    with pytest.raises(ValueError):guarded_patch({**before,'other':'edit'},before,patch,allowed={'x'})
    with pytest.raises(ValueError):inverse_patch({**before,**patch,'other':'edit'},before=before,applied_patch=patch)

def test_protected_media_and_extra_fields_never_patched():
    before={'listing_id':'EF-2611-ABCD','cloudinary_image_urls':'keep'}
    with pytest.raises(ValueError):guarded_patch(before,before,{'cloudinary_image_urls':'replace'},allowed={'cloudinary_image_urls'})
    with pytest.raises(ValueError):guarded_patch(before,before,{'unreviewed':'x'},allowed={'x'})
