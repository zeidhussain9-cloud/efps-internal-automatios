"""Live Inventory Stage-1 intake adapter; delegates processing to the canonical package."""
from __future__ import annotations
import json,time
from dataclasses import dataclass
import intake,pipeline
from shared.google_sheets import schema
from shared.google_sheets.client import GoogleSheetsClient
from shared.whatsapp_whapi.webhook import IncomingMessage
SESSION_PREFIX="inventory:"
@dataclass
class StoredSession:
 sender:str;listing_id:str="";started_at:str="";messages:list[dict]|None=None;seen_message_ids:list[str]|None=None
 def __post_init__(self):self.messages=self.messages or [];self.seen_message_ids=self.seen_message_ids or []
 @property
 def raw_text(self):return "\n".join(f"[{m['timestamp']}] [{m['message_id']}] {m['text']}".strip() for m in self.messages)
class DynamoSessionStore:
 def __init__(self,_res=None):self._res=_res
 def _table(self):
  if self._res is not None:return self._res.Table("efps-sessions")
  import boto3;return boto3.resource("dynamodb").Table("efps-sessions")
 def get(self,sender):
  item=self._table().get_item(Key={"user_id":SESSION_PREFIX+sender}).get("Item")
  if not item:return None
  return StoredSession(sender,str(item.get("listing_id") or ""),str(item.get("started_at") or ""),json.loads(item.get("messages_json") or "[]"),json.loads(item.get("seen_ids_json") or "[]"))
 def put(self,s):self._table().put_item(Item={"user_id":SESSION_PREFIX+s.sender,"listing_id":s.listing_id,"started_at":s.started_at,"messages_json":json.dumps(s.messages),"seen_ids_json":json.dumps(s.seen_message_ids),"expires_at":int(time.time())+86400})
 def delete(self,sender):self._table().delete_item(Key={"user_id":SESSION_PREFIX+sender})
def _rows(c):
 raw=c.read_range(schema.SHEET_ID,schema.WORKSHEET_NAME,"A2:AT");rows=[]
 for i,r in enumerate(raw):
  values=list(r)+[""]*(schema.GRID_WIDTH-len(r)) if len(r)<schema.GRID_WIDTH else list(r)
  if values:rows.append((i+2,schema.row_to_mapping(values)))
 return rows
def _find(c,lid):return next(((n,r) for n,r in _rows(c) if str(r.get("listing_id",""))==lid),None)
def _persist_initial(c,s):c.append_rows(schema.SHEET_ID,schema.WORKSHEET_NAME,[schema.mapping_to_row(pipeline.initial_row(s.listing_id,s.raw_text,s.started_at))])
def _persist_update(c,n,row):
 c.write_range(schema.SHEET_ID,schema.WORKSHEET_NAME,schema.range_for("intake_status","intake_status",n),[[row.get("intake_status","")]])
 c.write_range(schema.SHEET_ID,schema.WORKSHEET_NAME,schema.range_for("raw_message_text","raw_message_text",n),[[row.get("raw_message_text","")]])
def _close(c,s):
 if not s:return {"closed":False}
 found=_find(c,s.listing_id)
 if not found:return {"closed":False,"listing_id":s.listing_id,"reason":"sheet row not found"}
 n,row=found;out,issues=pipeline.process_closed_session(s.raw_text,row=row);pipeline.write_phase1_update(c,n,out);return {"closed":True,"listing_id":s.listing_id,"issues":issues}
def handle(message:IncomingMessage,*,store=None,client=None):
 if not message.is_inventory_listener or message.is_group or message.from_me:return {"inventory":False,"reason":"not inventory listener"}
 store=store or DynamoSessionStore();client=client or GoogleSheetsClient();sender=str(message.sender or message.chat_id).strip();session=store.get(sender);text=str(message.body or "").strip()
 if intake.is_new_marker(text):
  closed=_close(client,session);store.delete(sender);store.put(StoredSession(sender,started_at=str(message.timestamp or "")));return {"inventory":True,"recorded":False,"reason":"boundary opened","closed":closed}
 if not session:return {"inventory":True,"recorded":False,"reason":"before first NEW"}
 mid=message.message_id
 if mid and mid in session.seen_message_ids:return {"inventory":True,"recorded":False,"duplicate":True}
 if mid:session.seen_message_ids.append(mid)
 if message.message_type.lower() in {"image","video","document","audio"}:store.put(session);return {"inventory":True,"recorded":True,"media":True,"listing_id":session.listing_id}
 if text:session.messages.append({"text":text,"timestamp":message.timestamp or "","message_id":mid or ""})
 if not session.listing_id:session.listing_id=pipeline.next_listing_id(client);_persist_initial(client,session)
 else:
  found=_find(client,session.listing_id)
  if found:_persist_update(client,found[0],{**found[1],"raw_message_text":session.raw_text,"intake_status":"Raw"})
 store.put(session);return {"inventory":True,"recorded":True,"listing_id":session.listing_id}
