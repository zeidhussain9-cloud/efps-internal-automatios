"""Inventory webhook adapter for the two dedicated inventory sender numbers."""
from __future__ import annotations
from .intake import ingest, InMemorySessionStore
from .pipeline import initial_row, next_listing_id, process_closed_session, write_new_property

DEFAULT_STORE=InMemorySessionStore()

def handle(message:dict, *, store=None, sheets_client=None, maps_client=None, ai_llm=None):
    store=store or DEFAULT_STORE
    state,session=ingest(message,store)
    if state!='closed': return {'state':state}
    if sheets_client is None:
        return {'state':'closed','raw_text':session.raw_text,'image_count':session.image_count}
    lid=next_listing_id(sheets_client)
    row=initial_row(lid,session.raw_text,str(message.get('chat_id','')))
    processed,issues=process_closed_session(session.raw_text,row=row,maps_client=maps_client,ai_llm=ai_llm)
    write_new_property(sheets_client,processed)
    return {'state':'processed','listing_id':lid,'issues':issues,'image_count':session.image_count}
