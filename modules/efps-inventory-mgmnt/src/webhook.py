"""Inventory webhook adapter for the two dedicated inventory sender numbers."""
from __future__ import annotations
from .intake import ingest,InMemorySessionStore,PropertySession
from .pipeline import initial_row,next_listing_id,process_closed_session,write_new_property
from shared.google_sheets import schema

DEFAULT_STORE=InMemorySessionStore()

def _value(message,key,default=''):
    return getattr(message,key,default) if hasattr(message,key) else message.get(key,default)

def _find_row(client,listing_id):
    rows=client.read_range(schema.SHEET_ID,schema.WORKSHEET_NAME,schema.full_range(2))
    for i,row in enumerate(rows,start=2):
        if row and str(row[0]).strip()==listing_id:return i
    return None

def _persist_raw(client,session):
    n=_find_row(client,session.listing_id)
    if n is None:raise RuntimeError(f'listing_id not found: {session.listing_id}')
    row=schema.row_to_mapping(client.read_range(schema.SHEET_ID,schema.WORKSHEET_NAME,schema.full_range(n))[0])
    row['raw_message_text']=session.raw_text;row['intake_status']='Raw'
    client.write_row(schema.SHEET_ID,schema.WORKSHEET_NAME,n,schema.mapping_to_row(row))

def handle(message,*,store=None,sheets_client=None,maps_client=None,ai_llm=None):
    store=store or DEFAULT_STORE
    state,session=ingest(message,store)
    if state=='opened' and sheets_client is not None:
        session.listing_id=next_listing_id(sheets_client); session.source_group=str(_value(message,'chat_id'))
        write_new_property(sheets_client,initial_row(session.listing_id,'',session.source_group));store.put(session)
        return {'state':'opened','listing_id':session.listing_id}
    if state=='collecting' and sheets_client is not None:
        _persist_raw(sheets_client,session);return {'state':'collecting','listing_id':session.listing_id,'image_count':session.image_count}
    if state!='closed':return {'state':state}
    if sheets_client is None:return {'state':'closed','raw_text':session.raw_text,'image_count':session.image_count}
    n=_find_row(sheets_client,session.listing_id)
    if n is None:raise RuntimeError(f'closed session row missing: {session.listing_id}')
    existing=schema.row_to_mapping(sheets_client.read_range(schema.SHEET_ID,schema.WORKSHEET_NAME,schema.full_range(n))[0])
    existing['raw_message_text']=session.raw_text
    processed,issues=process_closed_session(session.raw_text,row=existing,maps_client=maps_client,ai_llm=ai_llm)
    sheets_client.write_row(schema.SHEET_ID,schema.WORKSHEET_NAME,n,schema.mapping_to_row(processed))
    return {'state':'processed','listing_id':session.listing_id,'issues':issues,'image_count':session.image_count}
