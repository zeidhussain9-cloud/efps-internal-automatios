"""Lead DynamoDB state access."""
from __future__ import annotations
import sys
from datetime import datetime,timezone
import audit,config
TABLES={config.DDB_LEADS:{"hash_key":"phone_number"},config.DDB_INTERACTIONS:{"hash_key":"phone_number","range_key":"timestamp"},config.DDB_SESSIONS:{"hash_key":"user_id"},config.DDB_AUDIT:{"hash_key":"phone_number","range_key":"changed_at"},config.DDB_BUGS:{"hash_key":"bug_id"}}
class DbError(RuntimeError):pass
def _resource(_res=None):
 if _res is not None:return _res
 import boto3;return boto3.resource("dynamodb",region_name=config.AWS_REGION)
def _table(name,_res=None):
 if _res is None and "pytest" in sys.modules:raise RuntimeError(f"refusing live {name} table in test")
 return _resource(_res).Table(name)
def put_lead(lead,*,_res=None):
 phone=str(lead.get("phone_number") or "").strip()
 if not phone:raise DbError("leads: phone_number is required")
 item={k:v for k,v in lead.items() if str(v).strip()!=""};item["phone_number"]=phone;item.setdefault("created_at",datetime.now(timezone.utc).isoformat());item["updated_at"]=datetime.now(timezone.utc).isoformat();old=_table(config.DDB_LEADS,_res).put_item(Item=item,ReturnValues="ALL_OLD").get("Attributes")
 try:audit.record(phone,audit.diff(old,item),_res=_res)
 except Exception as exc:print(f"audit skipped: {exc!r}")
 return item
def get_lead(phone,*,_res=None):
 key=str(phone or "").strip();return _table(config.DDB_LEADS,_res).get_item(Key={"phone_number":key}).get("Item") if key else None
def all_leads(*, _res=None):
 table=_table(config.DDB_LEADS,_res);items=[];kwargs={}
 while True:
  page=table.scan(**kwargs);items.extend(page.get("Items",[]));start=page.get("LastEvaluatedKey")
  if not start:return items
  kwargs["ExclusiveStartKey"]=start
def log_interaction(phone,direction,body,*,message_id="",group_name="",has_media=False,media_urls="",is_from_group=False,_res=None):
 if direction not in ("in","out"):raise DbError("direction must be 'in' or 'out'")
 item={"phone_number":str(phone).strip(),"timestamp":datetime.now(timezone.utc).isoformat(),"message_id":message_id,"direction":direction,"message_body":body,"group_name":group_name,"has_media":bool(has_media),"media_urls":media_urls,"is_from_group":bool(is_from_group)};_table(config.DDB_INTERACTIONS,_res).put_item(Item=item);return item
def lead_history(phone,limit=50,*,_res=None):
 key=str(phone or "").strip();return _table(config.DDB_INTERACTIONS,_res).query(KeyConditionExpression="phone_number = :p",ExpressionAttributeValues={":p":key},ScanIndexForward=True,Limit=limit).get("Items",[]) if key else []
def interaction_exists(phone,message_id,*,_res=None):
 if not message_id:return False
 return bool(_table(config.DDB_INTERACTIONS,_res).query(KeyConditionExpression="phone_number = :p",FilterExpression="message_id = :m",ExpressionAttributeValues={":p":str(phone).strip(),":m":str(message_id)},ScanIndexForward=False,Limit=100).get("Items"))
def set_card_ts(phone,card_ts,*,_res=None):_table(config.DDB_LEADS,_res).update_item(Key={"phone_number":str(phone).strip()},UpdateExpression="SET card_ts = :t",ExpressionAttributeValues={":t":card_ts})
