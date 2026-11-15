from src import pipeline_v5,notion_intake

RAW='''Semi Furnished 2 BHK with 2 Bathrooms
Rent:40K
Deposit:6 months
Carpet area:1200 sqft
No balcony
Gated Community
Location:Haralur
Preferred tenant:Open For All
Pets:No'''

def render(row,raw):return notion_intake.build_whatsapp_post(row,raw,maps_verified=True)
def route(bhk):return notion_intake._bhk_group(bhk)
def initial():return {'listing_id':'EF-2611-ABCD','cloudinary_image_urls':'https://example.test/1.jpg','listing_state':'Available','onboarded_on':'2026-11-15T09:11:00Z'}

def test_v5_pipeline_new_input_typed_rules_and_readiness():
    result=pipeline_v5.project(RAW,existing=initial(),render_caption=render,route_bhk=route)
    row=result['row']
    assert row['flat_furnishings']=='Semi Package'
    assert row['society_amenities']=='Premium Amenities'
    assert row['balconies']=='0'
    assert row['built_up_area']=='1290'
    assert row['carpet_area']=='1200'
    assert row['security_deposit']=='240000'
    assert row['pet_friendly']=='No'
    assert row['bachelor_preference']==''
    assert row['Live On']==[]
    assert row['onboarded_at']=='2026-11-15T09:11:00+00:00'
    assert row['onboarded_on']=='Sunday, November 15, 2026 at 02:41:00 pm'
    assert row['Pipeline Status']=='Ready to Post',result['issues']
    assert 'Pets: Not Allowed' in row['whatsapp_post']

def test_existing_posted_ids_do_not_fail_content_validation():
    result=pipeline_v5.project(RAW,existing={**initial(),'meta_catalog_id':'real-product-id','meta_catalog_status':'Posted','posted_url':'https://example.test/existing'},render_caption=render,route_bhk=route)
    assert not any('must remain empty' in issue for issue in result['issues'])
    assert result['row']['meta_catalog_id']=='real-product-id'
    assert result['row']['Pipeline Status']=='Ready to Post'

def test_raw_reprocess_manual_value_kept_and_conflict_reviewed():
    result=pipeline_v5.project(RAW,existing={**initial(),'monthly_rent':'41000'},provenance={'monthly_rent':{'origin':'manual'}},render_caption=render,route_bhk=route)
    assert result['row']['monthly_rent']=='41000'
    assert result['row']['Pipeline Status']=='Needs Review'
    assert 'monthly_rent' in result['conflicts']
    assert result['provenance']['monthly_rent']['origin']=='manual'

def test_manual_route_kept_but_invalid_bhk_never_ready():
    result=pipeline_v5.project(RAW.replace('2 BHK','6 BHK'),existing={**initial(),'WhatsApp Group':'Owner route'},provenance={'WhatsApp Group':{'origin':'manual'}},render_caption=render,route_bhk=route)
    assert result['row']['WhatsApp Group']=='Owner route'
    assert result['row']['Pipeline Status']=='Needs Review'

def test_blank_missing_photos_not_ready():
    result=pipeline_v5.project(RAW,existing={**initial(),'cloudinary_image_urls':''},render_caption=render,route_bhk=route)
    assert result['row']['Pipeline Status']=='Needs Review'
    assert 'Photos missing' in result['issues']

def test_stale_derived_provenance_does_not_overwrite_unacknowledged_human_value():
    result=pipeline_v5.project(RAW,existing={**initial(),'monthly_rent':'41000'},provenance={'monthly_rent':{'origin':'derived','last_generated_value':'40000'}},render_caption=render,route_bhk=route)
    assert result['row']['monthly_rent']=='41000'
    assert 'monthly_rent' in result['conflicts']
    assert result['row']['Pipeline Status']=='Needs Review'

def test_matching_manual_package_keeps_manual_ownership():
    result=pipeline_v5.project(RAW,existing={**initial(),'flat_furnishings':'Semi Package'},provenance={'flat_furnishings':{'origin':'manual'}},render_caption=render,route_bhk=route)
    assert result['provenance']['flat_furnishings']['origin']=='manual'

def test_manual_blank_caption_is_never_regenerated():
    result=pipeline_v5.project(RAW,existing={**initial(),'whatsapp_post':''},provenance={'whatsapp_post':{'origin':'manual'}},render_caption=render,route_bhk=route)
    assert result['row']['whatsapp_post']==''
    assert 'whatsapp_post' in result['conflicts']
    assert result['row']['Pipeline Status']=='Needs Review'


def test_equal_legacy_package_is_never_promoted_then_overwritten():
    first=pipeline_v5.project(RAW,existing={**initial(),'flat_furnishings':'Semi Package','society_amenities':'Premium Amenities','bachelor_preference':''},render_caption=render,route_bhk=route)
    assert first['provenance']['flat_furnishings']['origin']=='legacy_unknown'
    assert first['provenance']['society_amenities']['origin']=='legacy_unknown'
    second=pipeline_v5.project(RAW.replace('Semi Furnished','Fully Furnished'),existing=first['row'],provenance=first['provenance'],render_caption=render,route_bhk=route)
    assert second['row']['flat_furnishings']=='Semi Package'
    assert 'flat_furnishings' in second['conflicts']

def test_two_successive_generated_rent_updates_advance_acknowledgement():
    first=pipeline_v5.project(RAW,existing={**initial(),'monthly_rent':'39000'},provenance={'monthly_rent':{'origin':'derived','last_generated_value':'39000'}},render_caption=render,route_bhk=route)
    assert first['row']['monthly_rent']=='40000'
    assert first['provenance']['monthly_rent']['last_generated_value']=='40000'
    second=pipeline_v5.project(RAW.replace('Rent:40K','Rent:42K'),existing=first['row'],provenance=first['provenance'],render_caption=render,route_bhk=route)
    assert second['row']['monthly_rent']=='42000'
    assert second['provenance']['monthly_rent']['last_generated_value']=='42000'
    assert 'monthly_rent' not in second['conflicts']
