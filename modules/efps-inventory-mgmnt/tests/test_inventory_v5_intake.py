from copy import deepcopy
import pytest
from src.inventory_v5 import content_hash,AVAILABILITY,PIPELINE,CHANNELS,FULL_ITEMS,SEMI_ITEMS,STANDARD_ITEMS
from src.inventory_v5_intake import destination_candidate,existing_destination_plan,IntakeDestinationBlocked,validate_destination_schema


def fixture():
    row={'listing_id':'EF-2611-ABCD','furnish_type':'Semi Furnished','flat_furnishings':SEMI_ITEMS,
         'internal_property_type':'Semi Gated','society_amenities':STANDARD_ITEMS,
         'preferred_tenant_type':'Family','bachelor_preference':'','BHK':'2 BHK',
         'monthly_rent':25000,'raw_message_text':'original source','cloudinary_image_urls':'original media',
         'catalog_title':'catalog name','status':'Pending','listing_state':'Available','intake_status':'Processed'}
    schema={k:{'id':k,'type':'rich_text'}for k in row if k not in ('status','listing_state','intake_status')}
    schema['monthly_rent']={'id':'rent','type':'number'}
    for field,options in [('furnish_type',['Semi Furnished','Fully Furnished']),('flat_furnishings',['Semi Package','Full Package']),
        ('internal_property_type',['Standalone','Semi Gated','Gated Community']),('society_amenities',['Standard Amenities','Premium Amenities']),
        ('property_subtype',['Apartment','Villa','Independent House','Duplex','Studio','Independent Floor']),('preferred_tenant_type',['Family Only','Open For All']),('bachelor_preference',['-','Male Only','Female Only']),('BHK',['2 BHK'])]:
        schema[field]={'id':field,'type':'select','select':{'options':[{'name':x}for x in options]}}
    schema['SL number']={'id':'title','type':'title'}
    schema['_SL numeric sort']={'id':'sort','type':'formula','formula':{'expression':'toNumber(prop("SL number"))'}}
    for field,kind,options in [('Availability','select',AVAILABILITY),('Pipeline Status','select',PIPELINE),('Live On','multi_select',CHANNELS)]:
        schema[field]={'id':field,'type':kind,kind:{'options':[{'name':x}for x in options]}}
    return row,schema


def candidate(row,schema):return destination_candidate(row,schema=schema,sealed_schema_hash=content_hash(schema))


def test_exact_package_projection_and_separate_status_without_title_invention():
    row,schema=fixture();before=deepcopy(row);out=candidate(row,schema)
    assert out['flat_furnishings']=='Semi Package' and out['society_amenities']=='Standard Amenities'
    assert out['preferred_tenant_type']=='Family Only' and out['bachelor_preference']=='-'
    assert out['raw_message_text']==row['raw_message_text'] and out['cloudinary_image_urls']==row['cloudinary_image_urls']
    assert not {'Property','SL number','Availability','Pipeline Status','Live On','status','intake_status','listing_state'}&set(out)
    assert row==before


@pytest.mark.parametrize('field,value',[('flat_furnishings',SEMI_ITEMS+', AC'),('society_amenities','Private Pool'),('BHK','6 BHK'),('preferred_tenant_type','Students'),('bachelor_preference','Female Only')])
def test_custom_unknown_conflicting_values_require_review(field,value):
    row,schema=fixture();row[field]=value
    with pytest.raises(IntakeDestinationBlocked):candidate(row,schema)


@pytest.mark.parametrize('field,value',[('SL number','1'),('Availability','Rented Out'),('Pipeline Status','Ready to Post'),('Live On',['WhatsApp Group'])])
def test_source_cannot_supply_canonical_state(field,value):
    row,schema=fixture();row[field]=value
    with pytest.raises(IntakeDestinationBlocked):candidate(row,schema)


def test_changed_schema_unknown_fields_and_invalid_ids_refuse():
    row,schema=fixture()
    with pytest.raises(IntakeDestinationBlocked):destination_candidate(row,schema=schema,sealed_schema_hash='a'*64)
    row['unknown_source_field']='important detail'
    with pytest.raises(IntakeDestinationBlocked,match='Unmapped'):candidate(row,schema)
    row.pop('unknown_source_field');row['listing_id']='bad'
    with pytest.raises(IntakeDestinationBlocked,match='identity'):candidate(row,schema)


def plan(candidate,current,provenance):return existing_destination_plan(candidate=candidate,current=current,acknowledged=deepcopy(current),provenance=provenance,listing_id='EF-2611-ABCD')


def test_generated_update_narrow_manual_and_legacy_unknown_preserved():
    row={'listing_id':'EF-2611-ABCD','monthly_rent':25000,'security_deposit':100000,'whatsapp_post':'manual caption','Availability':'On Hold','Live On':['Meta Catalogue']}
    provenance={'monthly_rent':{'origin':'derived','last_generated_value':'25000'},'whatsapp_post':{'origin':'manual'}}
    out=plan({'monthly_rent':26000,'security_deposit':110000,'whatsapp_post':'generated new'},row,provenance)
    assert out['patch']=={'monthly_rent':26000,'Pipeline Status':'Needs Review'}
    assert out['conflicts']==['security_deposit','whatsapp_post']
    assert out['provenance']['whatsapp_post']['origin']=='manual'
    assert not out['source_completion_allowed']
    assert row['Availability']=='On Hold' and row['Live On']==['Meta Catalogue']


def test_matching_value_does_not_promote_owner_or_legacy_provenance():
    row={'listing_id':'EF-2611-ABCD','monthly_rent':25000}
    out=plan({'monthly_rent':'25000'},row,{})
    assert out['patch']=={} and out['provenance']=={}


def test_source_media_identity_catalog_and_history_never_overwritten():
    row={'listing_id':'EF-2611-ABCD','raw_message_text':'old raw','cloudinary_image_urls':'old media','catalog_title':'owner catalog','onboarded_on':'old date','SL number':'8','Availability':'On Hold','Live On':['Housing.com']}
    out=plan({k:('new'if not isinstance(v,list)else[])for k,v in row.items()if k!='listing_id'},row,{k:{'origin':'derived','last_generated_value':v}for k,v in row.items()})
    assert out['patch']=={'Pipeline Status':'Needs Review'}
    assert set(out['conflicts'])==set(row)-{'listing_id'}


def test_unacknowledged_edit_blocks_before_patch_and_archived_identity_refuse():
    row={'listing_id':'EF-2611-ABCD','monthly_rent':26000}
    with pytest.raises(IntakeDestinationBlocked,match='owner edits'):existing_destination_plan(candidate={},current=row,acknowledged={**row,'monthly_rent':25000},provenance={},listing_id=row['listing_id'])
    with pytest.raises(IntakeDestinationBlocked,match='Lifecycle'):plan({},dict(row,_archived=True),{})
    with pytest.raises(IntakeDestinationBlocked,match='binding'):existing_destination_plan(candidate={},current=row,acknowledged=row,provenance={},listing_id='EF-2611-ZZZZ')


def test_unconverted_package_field_or_multiple_titles_are_not_final_schema():
    row,schema=fixture();schema['flat_furnishings']['type']='rich_text'
    with pytest.raises(IntakeDestinationBlocked,match='incomplete'):candidate(row,schema)
    row,schema=fixture();schema['Property']={'id':'oldtitle','type':'title'}
    with pytest.raises(IntakeDestinationBlocked,match='title'):candidate(row,schema)


def test_low_level_plan_cannot_receive_source_pipeline_status():
    row={'listing_id':'EF-2611-ABCD','Pipeline Status':'Needs Review'}
    with pytest.raises(IntakeDestinationBlocked,match='pipeline'):plan({'Pipeline Status':'Ready to Post'},row,{})
