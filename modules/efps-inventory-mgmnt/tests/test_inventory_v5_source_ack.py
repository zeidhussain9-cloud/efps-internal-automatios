from copy import deepcopy
import pytest
from test_inventory_v5_intake_binding import port,db,SOURCE,PAGE
from src.inventory_v5_source_ack import capture_upstream_output,prepare_source_write
from src.inventory_v5 import content_hash
from src.inventory_v5_intake import IntakeDestinationBlocked
from src.inventory_v5_adapter import serialize_notion
from src.inventory_v5_intake_binding import INTAKE_DATABASE_ID


def setup(db,status='Pending',issues=None):
    args,c,s,client,resolver=port(db)
    args['processed']['status']=status
    args['processed']['intake_status']='Processed'
    # Prior fixture output already carries these legacy statuses.
    outcome=capture_upstream_output(source_page_id=SOURCE,payload_hash=args['payload_hash'],processed=args['processed'],issues=issues or [],
        submissions=args['submissions'],destination_schema=args['notion'].schema,sealed_destination_hash=args['sealed_schema_hash'])
    client.source['properties']['Processing Notes']={'type':'rich_text',**serialize_notion('old notes','rich_text')}
    client.source['properties']['Processed At']={'type':'date','date':None}
    schema={k:{'id':k,'type':v['type']}for k,v in client.source['properties'].items()}
    schema['Processed Property']['relation']={'database_id':'bccfd4f55e294b269daa093a928f873a'}
    schema['Intake Status']['status']={'options':[{'name':x}for x in ('Processing','Processed','Needs Review')]}
    kw=dict(source_page_id=SOURCE,payload_hash=args['payload_hash'],submissions=args['submissions'],resolver=resolver,
            source_schema_loader=lambda:deepcopy(schema),sealed_source_hash=content_hash(schema),processed_at='2026-11-15T18:52:00+00:00')
    return args,c,s,client,resolver,outcome,schema,kw


def test_saved_legacy_output_generates_exact_source_contract_without_patch_or_completion(db):
    args,c,s,client,resolver,outcome,schema,kw=setup(db)
    plan=prepare_source_write(**kw)
    assert plan['properties']['Intake Status']['status']['name']=='Processed'
    assert plan['properties']['Processing Notes']['rich_text'][0]['text']['content']=='old notes\nProcessed through the canonical EFPS inventory pipeline.'
    assert plan['properties']['Processed Property']=={'relation':[{'id':PAGE}]}
    assert not plan['source_completion_allowed'] and plan['effect_required']
    x=db.request('__inspect')['submissions'][0]
    assert x['upstream_outcome']==outcome and x['source_write_plan']==plan
    assert x['phase']=='awaiting_source_ack' and client.source['properties']['Intake Status']['status']['name']=='Processing'
    assert s.count==1 and prepare_source_write(**kw)==plan


def test_review_output_and_notes_stay_separate_from_availability(db):
    args,c,s,client,resolver,outcome,schema,kw=setup(db,'Needs Review',['Maps verification failed'])
    plan=prepare_source_write(**kw)
    assert plan['status']=='Needs Review'
    assert 'Maps verification failed' in plan['properties']['Processing Notes']['rich_text'][0]['text']['content']
    assert not {'Availability','Live On','Pipeline Status'}&set(plan['properties'])


def test_processed_caller_cannot_capture_success_or_replace_saved_output(db):
    args,c,s,client,resolver,outcome,schema,kw=setup(db)
    common=dict(source_page_id=SOURCE,payload_hash=args['payload_hash'],submissions=args['submissions'],destination_schema=args['notion'].schema,sealed_destination_hash=args['sealed_schema_hash'])
    with pytest.raises(IntakeDestinationBlocked):capture_upstream_output(**common,processed={**args['processed'],'status':'Processed'},issues=[])
    with pytest.raises(RuntimeError):capture_upstream_output(**common,processed={**args['processed'],'status':'Needs Review'},issues=[])
    assert db.request('__inspect')['submissions'][0]['upstream_outcome']==outcome


def test_changed_processed_candidate_schema_or_source_refuses(db):
    args,c,s,client,resolver,outcome,schema,kw=setup(db)
    schema['Processed At']['type']='rich_text'
    with pytest.raises(IntakeDestinationBlocked,match='seal'):prepare_source_write(**kw)
    schema['Processed At']['type']='date'
    client.source['properties']['Raw Property Data']={'type':'rich_text',**serialize_notion('new raw','rich_text')}
    with pytest.raises(IntakeDestinationBlocked,match='payload'):prepare_source_write(**kw)


def test_missing_outcome_and_qualified_time_are_not_inferred(db):
    args,c,s,client,resolver=port(db)
    with pytest.raises(IntakeDestinationBlocked,match='timezone'):prepare_source_write(source_page_id=SOURCE,payload_hash=args['payload_hash'],submissions=args['submissions'],resolver=resolver,source_schema_loader=lambda:{},sealed_source_hash='a'*64,processed_at='2026-11-15T18:00:00')
    with pytest.raises(IntakeDestinationBlocked,match='Saved upstream'):prepare_source_write(source_page_id=SOURCE,payload_hash=args['payload_hash'],submissions=args['submissions'],resolver=resolver,source_schema_loader=lambda:{},sealed_source_hash='a'*64,processed_at='2026-11-15T18:00:00Z')


def test_destination_revision_drift_cannot_prepare_source_processed(db):
    args,c,s,client,resolver,outcome,schema,kw=setup(db)
    w=args['workers'];lease=w.claim(PAGE);w.load(PAGE,lease)
    w.finish(PAGE,lease,args['notion'].snapshot(PAGE),status='self_write_acknowledged');w.release(PAGE,lease)
    with pytest.raises(RuntimeError):prepare_source_write(**kw)
    assert db.request('__inspect')['submissions'][0]['source_write_plan'] is None


def effect_setup(db):
    from src.inventory_v5_source_ack import SourceEffectPreparation
    args,c,s,client,resolver,outcome,schema,kw=setup(db)
    plan=prepare_source_write(**kw)
    record=args['submissions'].call('claim_existing',SOURCE)
    effect=SourceEffectPreparation(args['submissions'],SOURCE,record['lease_token'])
    ticket=effect.begin(source=deepcopy(client.source),source_schema=deepcopy(schema))
    return args,c,s,client,schema,plan,effect,ticket['effect_id']


def readback_for(client,plan):
    out=deepcopy(client.source)
    for name,value in plan['properties'].items():out['properties'][name]={'type':next(iter(value)),**deepcopy(value)}
    return out


def test_durable_source_effect_receipt_readback_finish_preparation_without_source_patch(db):
    args,c,s,client,schema,plan,effect,nonce=effect_setup(db)
    dispatch={'effect_id':nonce,'method':'PATCH','page_id':SOURCE,'body_hash':plan['body_hash']}
    effect.bind(nonce,plan['body_hash'])
    effect.receipt(nonce,{'status':200,'request_id':'synthetic-source-terminal','dispatch':dispatch})
    effect.finish_prepare(nonce,readback_for(client,plan))
    x=db.request('__inspect')['submissions'][0]
    assert x['source_effect']['status']=='finish_prepared' and x['phase']=='awaiting_source_ack'
    assert x['source_effect']['readback']==plan['expected_after']
    assert s.count==1 and client.source['properties']['Intake Status']['status']['name']=='Processing'
    assert args['submissions'].call('claim_existing',SOURCE)['needs_source_effect_review']
    with pytest.raises(RuntimeError):args['submissions'].call('finish',SOURCE,effect.lease)


def test_unknown_source_flight_blocks_successor_without_timeout_clear(db):
    args,c,s,client,schema,plan,effect,nonce=effect_setup(db)
    effect.bind(nonce,plan['body_hash'])
    db.request('__expire')
    x=args['submissions'].call('claim_existing',SOURCE)
    assert x['busy'] and x['needs_source_effect_review']
    with pytest.raises(RuntimeError):effect.finish_prepare(nonce,readback_for(client,plan))
    assert s.count==1


def test_effect_nonce_dispatch_receipt_and_owner_readback_are_exact(db):
    args,c,s,client,schema,plan,effect,nonce=effect_setup(db)
    with pytest.raises(RuntimeError):effect.bind(nonce,'b'*64)
    effect.bind(nonce,plan['body_hash'])
    with pytest.raises(RuntimeError):effect.receipt(SOURCE,{'status':200,'request_id':'wrong','dispatch':{}})
    dispatch={'effect_id':nonce,'method':'PATCH','page_id':SOURCE,'body_hash':plan['body_hash']}
    with pytest.raises(RuntimeError):effect.receipt(nonce,{'status':504,'request_id':'unknown','dispatch':dispatch})
    effect.receipt(nonce,{'status':200,'request_id':'known','dispatch':dispatch})
    changed=readback_for(client,plan);changed['properties']['Raw Property Data']={'type':'rich_text',**serialize_notion('new owner raw','rich_text')}
    with pytest.raises(RuntimeError):effect.finish_prepare(nonce,changed)
    assert db.request('__inspect')['submissions'][0]['source_effect']['status']=='begun'


def test_begin_requires_exact_source_object_not_just_matching_claimed_hash(db):
    from src.inventory_v5_source_ack import SourceEffectPreparation
    args,c,s,client,resolver,outcome,schema,kw=setup(db);plan=prepare_source_write(**kw)
    record=args['submissions'].call('claim_existing',SOURCE)
    effect=SourceEffectPreparation(args['submissions'],SOURCE,record['lease_token'])
    changed=deepcopy(client.source);changed['last_edited_time']='changed'
    with pytest.raises(RuntimeError):effect.begin(source=changed,source_schema=schema)
    assert db.request('__inspect')['submissions'][0]['source_effect'] is None


def test_saved503_receipt_requires_exact_guidance_no_write_retry(db):
    args,c,s,client,schema,plan,effect,nonce=effect_setup(db)
    effect.bind(nonce,plan['body_hash'])
    dispatch={'effect_id':nonce,'method':'PATCH','page_id':SOURCE,'body_hash':plan['body_hash']}
    receipt={'status':503,'request_id':'saved-source','dispatch':dispatch,'code':'service_unavailable',
       'classification':'documented_saved_no_repeat','additional_data':{'retry_guidance':['Read the object again to confirm the saved change.','Do not repeat the write.']}}
    with pytest.raises(RuntimeError):effect.receipt(nonce,{**receipt,'additional_data':{}})
    effect.receipt(nonce,receipt);effect.finish_prepare(nonce,readback_for(client,plan))
    assert s.count==1 and db.request('__inspect')['submissions'][0]['phase']=='awaiting_source_ack'


def test_destination_drift_after_terminal_receipt_blocks_finish_preparation(db):
    args,c,s,client,schema,plan,effect,nonce=effect_setup(db)
    effect.bind(nonce,plan['body_hash'])
    effect.receipt(nonce,{'status':200,'request_id':'source-terminal','dispatch':{'effect_id':nonce,'method':'PATCH','page_id':SOURCE,'body_hash':plan['body_hash']}})
    w=args['workers'];lease=w.claim(PAGE);w.load(PAGE,lease)
    w.finish(PAGE,lease,args['notion'].snapshot(PAGE),status='self_write_acknowledged');w.release(PAGE,lease)
    with pytest.raises(RuntimeError):effect.finish_prepare(nonce,readback_for(client,plan))
    assert db.request('__inspect')['submissions'][0]['source_effect']['status']=='begun'


def test_source_schema_reread_exact_and_existing_notes_not_silently_deduplicated(db):
    args,c,s,client,resolver,outcome,schema,kw=setup(db)
    text='Processed through the canonical EFPS inventory pipeline.'
    client.source['properties']['Processing Notes']={'type':'rich_text',**serialize_notion(text,'rich_text')}
    plan=prepare_source_write(**kw)
    assert plan['properties']['Processing Notes']['rich_text'][0]['text']['content']==text+'\n'+text
