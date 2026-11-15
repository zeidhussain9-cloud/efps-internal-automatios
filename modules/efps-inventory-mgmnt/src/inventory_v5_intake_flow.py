"""Explicit staged existing-row orchestration, never a production route.

The initial pipeline row/client are supplied by staging. Only the actual shared
legacy final-processing body produces the captured output. It is frozen before
any destination effect, and restart never reruns extraction/media for a saved
output. An interrupted pre-capture run stays held, not automatically replayed.
"""
from copy import deepcopy
try:
    from . import notion_intake
    from .inventory_v5 import content_hash
    from .inventory_v5_intake import destination_candidate,validate_destination_schema,IntakeDestinationBlocked
    from .inventory_v5_intake_executor import save_existing_destination
    from .inventory_v5_source_ack import capture_upstream_output,complete_existing_source,handoff_completed_payload,validate_source_schema,source_values
except ImportError:
    import notion_intake
    from inventory_v5 import content_hash
    from inventory_v5_intake import destination_candidate,validate_destination_schema,IntakeDestinationBlocked
    from inventory_v5_intake_executor import save_existing_destination
    from inventory_v5_source_ack import capture_upstream_output,complete_existing_source,handoff_completed_payload,validate_source_schema,source_values


def run_existing_intake_staged(*,source_page_id,payload_hash,page_id,listing_id,
        initial_row,pipeline_client,cloudinary,maps_client,ola_client,
        workers,submissions,notion,schema_loader,sealed_schema_hash,resolver,
        source_schema_loader,sealed_source_hash,processed_at,source_http):
    schema=schema_loader();validate_destination_schema(schema,sealed_schema_hash=sealed_schema_hash)
    source_schema=source_schema_loader();validate_source_schema(source_schema,sealed_source_hash)
    source=resolver.source(source_page_id,listing_id,page_id)
    resolver.destination(listing_id,page_id)
    # Inputs, not completion fields/last-edit time, identify a rerunnable lookup.
    # Full typed raw/photo values are retained, so changed/expired source data
    # conservatively holds rather than silently rerunning media.
    source_projection=source_values(source)
    source_projection['values']={k:v for k,v in source_projection['values'].items()
        if k in ('Raw Property Data','Photos','Listing ID','Processed Property')}
    if initial_row.get('listing_id')!=listing_id:raise IntakeDestinationBlocked('Initial row identity differs')
    snapshot={'source':source_projection,'initial_row':deepcopy(initial_row),
              'destination_schema':schema,'source_schema':source_schema}
    ticket=submissions.call('begin_pipeline',source_page_id,page_id=page_id,
        payload_hash=payload_hash,listing_id=listing_id,plan=snapshot)
    if ticket.get('held'):return {'status':'pipeline_capture_held','source_completion_allowed':False}
    if ticket['run_allowed']:
        processed,issues=notion_intake.final_intake_output(page=deepcopy(source),listing_id=listing_id,
            row=deepcopy(initial_row),raw_text=notion_intake._plain_text(source['properties']['Raw Property Data']),
            notion=pipeline_client,cloudinary=cloudinary,maps_client=maps_client,ola_client=ola_client)
        # Preserve the exact output, never upgrade it to Processed here.
        output={'processed':deepcopy(processed),'issues':deepcopy(issues)}
        if resolver.source(source_page_id,listing_id,page_id)!=source or schema_loader()!=schema or source_schema_loader()!=source_schema:
            raise IntakeDestinationBlocked('Pipeline source/schema changed; captured run held')
        submissions.call('freeze_pipeline',source_page_id,ticket['token'],payload_hash=payload_hash,plan=output)
    else:output=ticket['output']
    processed=output['processed'];issues=output['issues']
    candidate=destination_candidate(processed,schema=schema,sealed_schema_hash=sealed_schema_hash)
    saved=submissions.call('claim_source',source_page_id)
    if saved.get('busy'):return {'status':'held','source_completion_allowed':False}
    if saved.get('found'):
        old_hash=saved['payload_hash'];lease=saved['lease_token']
        submissions.call('release',source_page_id,lease)
        if old_hash==payload_hash and (saved['phase']=='completed' or saved.get('source_effect') is not None):
            return complete_existing_source(source_page_id=source_page_id,payload_hash=payload_hash,submissions=submissions,
                resolver=resolver,source_schema_loader=source_schema_loader,sealed_source_hash=sealed_source_hash,
                processed_at=processed_at,workers=workers,notion=notion,destination_schema_loader=schema_loader,
                sealed_destination_hash=sealed_schema_hash,source_http=source_http)
        if old_hash!=payload_hash:
            handoff_completed_payload(source_page_id=source_page_id,submissions=submissions,source_client=resolver.client,
                processed=processed,destination_schema=schema,sealed_destination_hash=sealed_schema_hash)
    claim=submissions.call('claim',source_page_id,page_id=page_id,payload_hash=payload_hash,listing_id=listing_id,candidate=candidate)
    if claim.get('busy'):return {'status':'held','source_completion_allowed':False}
    submissions.call('release',source_page_id,claim['lease_token'])
    capture_upstream_output(source_page_id=source_page_id,payload_hash=payload_hash,processed=processed,issues=issues,
        submissions=submissions,destination_schema=schema,sealed_destination_hash=sealed_schema_hash)
    result=save_existing_destination(source_page_id=source_page_id,payload_hash=payload_hash,page_id=page_id,
        processed=processed,workers=workers,submissions=submissions,notion=notion,schema_loader=schema_loader,
        sealed_schema_hash=sealed_schema_hash,verify_binding=resolver)
    if result['status']!='awaiting_source_ack':return result
    return complete_existing_source(source_page_id=source_page_id,payload_hash=payload_hash,submissions=submissions,
        resolver=resolver,source_schema_loader=source_schema_loader,sealed_source_hash=sealed_source_hash,
        processed_at=processed_at,workers=workers,notion=notion,destination_schema_loader=schema_loader,
        sealed_destination_hash=sealed_schema_hash,source_http=source_http)
