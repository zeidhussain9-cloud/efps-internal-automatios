from copy import deepcopy
import pytest
from test_inventory_v5_source_ack import setup,db
from test_inventory_v5_intake_binding import SOURCE,PAGE
from src.inventory_v5_source_ack import complete_existing_source,handoff_completed_payload,prepare_source_write
from src.inventory_v5_http import V5HttpNotionClient
from src.inventory_v5_intake import IntakeDestinationBlocked
from src.inventory_v5_adapter import serialize_notion
from src.inventory_v5_intake_binding import source_payload_hash


def executor(db,fresh=False):
    args,c,s,client,resolver,outcome,schema,kw=setup(db,save=not fresh)
    orig=c.get_page;c.get_page=lambda page:{**orig(page),'id':PAGE}
    class Response:
        def __init__(self,code,body):self.ok=200<=code<300;self.status_code=code;self.body=body;self.headers={'x-request-id':'source-request-1'}
        def json(self):return self.body
    class Session:
        count=0;timeout=False;code=200;body={};request_id=True
        after_patch=lambda self:None
        def request(self,method,url,**options):
            assert method=='PATCH' and url.endswith('/'+SOURCE)
            self.count+=1
            for name,value in options['json']['properties'].items():client.source['properties'][name]={'type':next(iter(value)),**deepcopy(value)}
            self.after_patch()
            if self.timeout:raise TimeoutError('unknown source flight')
            response=Response(self.code,self.body)
            if not self.request_id:response.headers={}
            return response
    session=Session();http=V5HttpNotionClient(token='synthetic',version='2022-06-28',session=session)
    call={**kw,'workers':args['workers'],'notion':args['notion'],
      'destination_schema_loader':args['schema_loader'],'sealed_destination_hash':args['sealed_schema_hash'],'source_http':http}
    return call,args,c,s,client,session


def test_actual_http_response_readback_commit_and_repeat_zero_second_patch(db):
    call,args,c,s,client,http=executor(db)
    out=complete_existing_source(**call)
    assert out['source_completion_allowed'] and out['status']=='Processed' and http.count==1
    saved=db.request('__inspect')['submissions'][0]
    assert saved['phase']=='completed' and saved['source_effect']['status']=='committed'
    assert saved['source_effect']['receipt']['request_id']=='source-request-1'
    assert complete_existing_source(**call)['source_completion_allowed'] and http.count==1


@pytest.mark.parametrize('edit',['rent','identity','parent','archived'])
def test_unprocessed_live_destination_edit_before_source_patch_quarantines_original(db,edit):
    call,args,c,s,client,http=executor(db)
    if edit=='rent':c.update_page(PAGE,{'monthly_rent':serialize_notion(27000,'number')})
    elif edit=='identity':c.update_page(PAGE,{'listing_id':serialize_notion('EF-2611-ZZZZ','rich_text')})
    else:
        getter=c.get_page;c.get_page=lambda page:{**getter(page),**({'parent':{'database_id':SOURCE}}if edit=='parent'else{'archived':True})}
    with pytest.raises((ValueError,IntakeDestinationBlocked)):complete_existing_source(**call)
    x=db.request('__inspect')
    assert http.count==0 and x['mirror']['pipeline_status']=='Needs Review' and x['mirror']['business_status']=='Needs Review'
    assert x['submissions'][0]['phase']=='awaiting_source_ack'
    assert client.source['properties']['Intake Status']['status']['name']=='Processing'


def test_owner_edit_during_source_response_holds_completion_and_quarantines(db):
    call,args,c,s,client,http=executor(db)
    http.after_patch=lambda:c.update_page(PAGE,{'monthly_rent':serialize_notion(27000,'number')})
    with pytest.raises(IntakeDestinationBlocked):complete_existing_source(**call)
    x=db.request('__inspect');assert http.count==1 and x['submissions'][0]['phase']=='awaiting_source_ack'
    assert x['mirror']['pipeline_status']=='Needs Review'


def test_durable_terminal_receipt_restart_after_readback_loss_no_second_patch(db):
    call,args,c,s,client,http=executor(db)
    orig=args['submissions'].call
    def fail(op,*a,**kw):
        if op=='source_finish_prepare':raise TimeoutError('readback receipt ledger unavailable')
        return orig(op,*a,**kw)
    args['submissions'].call=fail
    with pytest.raises(TimeoutError):complete_existing_source(**call)
    assert db.request('__inspect')['submissions'][0]['source_effect']['receipt']['status']==200
    args['submissions'].call=orig;db.request('__expire')
    assert complete_existing_source(**call)['source_completion_allowed'] and http.count==1


@pytest.mark.parametrize('lost',['receipt','response','request_id'])
def test_source_unknown_flight_or_receipt_loss_never_resends_or_completes(db,lost):
    call,args,c,s,client,http=executor(db)
    if lost=='response':http.timeout=True
    elif lost=='request_id':http.request_id=False
    else:
        orig=args['submissions'].call
        def fail(op,*a,**kw):
            if op=='source_receipt':raise TimeoutError('receipt not saved')
            return orig(op,*a,**kw)
        args['submissions'].call=fail
    with pytest.raises((RuntimeError,TimeoutError)):complete_existing_source(**call)
    db.request('__expire')
    assert not complete_existing_source(**call)['source_completion_allowed'] and http.count==1
    assert db.request('__inspect')['submissions'][0]['phase']=='awaiting_source_ack'


def test_commit_response_loss_resumes_completed_version_without_second_patch(db):
    call,args,c,s,client,http=executor(db);orig=args['submissions'].call
    def fail(op,*a,**kw):
        result=orig(op,*a,**kw)
        if op=='source_commit':raise TimeoutError('commit response lost')
        return result
    args['submissions'].call=fail
    with pytest.raises(TimeoutError):complete_existing_source(**call)
    args['submissions'].call=orig
    assert complete_existing_source(**call)['source_completion_allowed'] and http.count==1


def test_documented_saved503_from_actual_http_never_repeats(db):
    call,args,c,s,client,http=executor(db);http.code=503
    http.body={'code':'service_unavailable','additional_data':{'retry_guidance':['Read the object again to confirm the saved change.','Do not repeat the write.']}}
    assert complete_existing_source(**call)['source_completion_allowed'] and http.count==1
    assert db.request('__inspect')['submissions'][0]['source_effect']['receipt']['status']==503


def test_source_owner_raw_edit_after_response_refuses_finish(db):
    call,args,c,s,client,http=executor(db)
    http.after_patch=lambda:client.source['properties'].update({'Raw Property Data':{'type':'rich_text',**serialize_notion('new input','rich_text')}})
    with pytest.raises(IntakeDestinationBlocked):complete_existing_source(**call)
    assert http.count==1 and db.request('__inspect')['submissions'][0]['phase']=='awaiting_source_ack'


def test_completed_version_handoff_preserves_evidence_and_blocks_old_payload(db):
    call,args,c,s,client,http=executor(db);complete_existing_source(**call)
    old=call['payload_hash']
    client.source['properties']['Raw Property Data']={'type':'rich_text',**serialize_notion('new raw','rich_text')}
    out=handoff_completed_payload(source_page_id=SOURCE,submissions=args['submissions'],source_client=client,
        processed=args['processed'],destination_schema=args['notion'].schema,sealed_destination_hash=args['sealed_schema_hash'])
    assert out['payload_hash']==source_payload_hash(client.source)!=old and not out['source_completion_allowed']
    saved=db.request('__inspect')['submissions'][0]
    assert saved['phase']=='claimed' and saved['source_effect'] is None and saved['upstream_outcome'] is None
    assert db.request('__inspect')['history'][0]['record']['source_effect']['receipt']['request_id']=='source-request-1'
    with pytest.raises(IntakeDestinationBlocked):complete_existing_source(**call)
    assert http.count==1


def flow(db,monkeypatch):
    from src import notion_intake
    from src.inventory_v5_intake_flow import run_existing_intake_staged
    call,args,c,s,client,http=executor(db,fresh=True)
    db.request('__legacy_binding',source_page_id=SOURCE,listing_id='EF-2611-ABCD',page_id=PAGE,payload_hash=args['payload_hash'])
    counts={'uploads':0,'pipeline':0,'caption':0}
    def uploads(*a,**kw):counts['uploads']+=1;return [],[]
    def pipeline(*a,**kw):counts['pipeline']+=1;return deepcopy(args['processed']),[]
    def caption(*a,**kw):counts['caption']+=1;return ''
    monkeypatch.setattr(notion_intake,'_upload_photos',uploads)
    monkeypatch.setattr(notion_intake.pipeline,'process_closed_session',pipeline)
    monkeypatch.setattr(notion_intake,'build_whatsapp_post',caption)
    class PipelineClient:
        _listing_schema={'locality':{'type':'select','select':{'options':[]}}}
    kwargs=dict(source_page_id=SOURCE,payload_hash=call['payload_hash'],page_id=PAGE,listing_id='EF-2611-ABCD',
        initial_row={'listing_id':'EF-2611-ABCD'},pipeline_client=PipelineClient(),cloudinary=object(),maps_client=object(),ola_client=object(),
        workers=args['workers'],submissions=args['submissions'],notion=args['notion'],schema_loader=args['schema_loader'],
        sealed_schema_hash=args['sealed_schema_hash'],resolver=call['resolver'],source_schema_loader=call['source_schema_loader'],
        sealed_source_hash=call['sealed_source_hash'],processed_at=call['processed_at'],source_http=call['source_http'])
    return lambda:run_existing_intake_staged(**kwargs),kwargs,counts,args,c,client,http


def test_actual_shared_pipeline_boundary_capture_save_source_finish_no_repeat(db,monkeypatch):
    run,kwargs,counts,args,c,client,http=flow(db,monkeypatch)
    out=run()
    assert out['source_completion_allowed'] and out['status']=='Needs Review'
    saved=db.request('__inspect')['submissions'][0]
    assert saved['upstream_outcome']['processed']['status']=='Needs Review'
    assert saved['upstream_outcome']['issues']==['WhatsApp caption not generated because a verified locality or Maps verification is missing.']
    assert counts=={'uploads':1,'pipeline':1,'caption':1} and http.count==1
    assert run()['source_completion_allowed'] and counts['uploads']==1 and http.count==1


def test_freeze_response_lost_resumes_saved_actual_output_without_media_replay(db,monkeypatch):
    run,kwargs,counts,args,c,client,http=flow(db,monkeypatch);orig=args['submissions'].call
    def lost(op,*a,**kw):
        value=orig(op,*a,**kw)
        if op=='freeze_pipeline':raise TimeoutError('freeze response lost')
        return value
    args['submissions'].call=lost
    with pytest.raises(TimeoutError):run()
    args['submissions'].call=orig
    assert run()['source_completion_allowed'] and counts['pipeline']==1 and http.count==1


def test_uncaptured_pipeline_interrupt_never_replays_uploads(db,monkeypatch):
    run,kwargs,counts,args,c,client,http=flow(db,monkeypatch);orig=args['submissions'].call
    def lost(op,*a,**kw):
        if op=='freeze_pipeline':raise TimeoutError('freeze never saved')
        return orig(op,*a,**kw)
    args['submissions'].call=lost
    with pytest.raises(TimeoutError):run()
    args['submissions'].call=orig
    assert run()['status']=='pipeline_capture_held' and counts['uploads']==1 and http.count==0


@pytest.mark.parametrize('barrier',['lease','row_busy','source_schema','destination_schema','binding'])
def test_before_http_checks_fail_closed(db,barrier):
    call,args,c,s,client,http=executor(db)
    if barrier=='row_busy':
        token=args['workers']._claim(PAGE,'claim_ack')
        assert not complete_existing_source(**call)['source_completion_allowed']
        args['workers'].release(PAGE,token)
    elif barrier=='lease':
        orig=args['workers'].renew
        def expired(*a,**kw):db.request('__expire');return orig(*a,**kw)
        args['workers'].renew=expired
        with pytest.raises(RuntimeError):complete_existing_source(**call)
    elif barrier=='source_schema':
        call['source_schema_loader']=lambda:{}
        with pytest.raises(IntakeDestinationBlocked):complete_existing_source(**call)
    elif barrier=='destination_schema':
        call['destination_schema_loader']=lambda:{}
        with pytest.raises(IntakeDestinationBlocked):complete_existing_source(**call)
        assert db.request('__inspect')['mirror']['pipeline_status']=='Needs Review'
    else:
        client.responses=[{'results':[],'has_more':False}]
        with pytest.raises(IntakeDestinationBlocked):complete_existing_source(**call)
        assert db.request('__inspect')['mirror']['pipeline_status']=='Needs Review'
    assert http.count==0 and db.request('__inspect')['submissions'][0]['phase']=='awaiting_source_ack'


def test_source_commit_requires_terminal_readback_and_live_row_lease(db):
    call,args,c,s,client,http=executor(db)
    record=args['submissions'].call('claim_source',SOURCE)
    with pytest.raises(RuntimeError):args['submissions'].call('source_commit',SOURCE,record['lease_token'],plan={})
    args['submissions'].call('release',SOURCE,record['lease_token'])
    orig=args['submissions'].call
    def stale(op,*a,**kw):
        if op=='source_commit':kw['plan']['row_lease']=SOURCE
        return orig(op,*a,**kw)
    args['submissions'].call=stale
    with pytest.raises(RuntimeError):complete_existing_source(**call)
    args['submissions'].call=orig
    assert db.request('__inspect')['submissions'][0]['phase']=='awaiting_source_ack'
    assert complete_existing_source(**call)['source_completion_allowed'] and http.count==1


def test_next_payload_runs_once_and_archives_prior_receipt_before_new_completion(db,monkeypatch):
    from src.inventory_v5_intake_flow import run_existing_intake_staged
    from src.inventory_v5_intake_binding import ExistingBindingResolver
    run,kwargs,counts,args,c,client,http=flow(db,monkeypatch)
    assert run()['source_completion_allowed']
    # A fresh source payload obtains its own actual run. The first version's
    # output/receipt stay in history; no reuse of old successful processing.
    client.source['properties']['Raw Property Data']={'type':'rich_text',**serialize_notion('a new source version','rich_text')}
    kwargs['payload_hash']=source_payload_hash(client.source)
    kwargs['resolver']=ExistingBindingResolver(client=client,request=db.request,payload_hash=kwargs['payload_hash'])
    # Simulated second HTTP server request reference is independently bound.
    session_request=http.request
    def request(*a,**kw):
        response=session_request(*a,**kw);response.headers={'x-request-id':'source-request-2'};return response
    http.request=request
    out=run_existing_intake_staged(**kwargs)
    assert out['source_completion_allowed'] and http.count==2 and counts['pipeline']==2
    x=db.request('__inspect')
    assert len(x['history'])==1 and len(x['pipeline_runs'])==2 and x['submissions'][0]['phase']=='completed'
    assert x['history'][0]['record']['source_effect']['receipt']['request_id']=='source-request-1'
    assert x['submissions'][0]['source_effect']['receipt']['request_id']=='source-request-2'


def test_intervening_ack_revision_is_quarantined_not_left_ready(db):
    call,args,c,s,client,http=executor(db)
    w=args['workers'];lease=w.claim(PAGE);w.load(PAGE,lease)
    w.finish(PAGE,lease,args['notion'].snapshot(PAGE),status='self_write_acknowledged');w.release(PAGE,lease)
    with pytest.raises(IntakeDestinationBlocked):complete_existing_source(**call)
    x=db.request('__inspect');assert x['mirror']['pipeline_status']=='Needs Review' and http.count==0
