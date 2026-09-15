"""Persistent Slack runtime bug register and operator report session."""
from __future__ import annotations
import json,os,uuid
from datetime import datetime,timezone

def _resource():
 import boto3;return boto3.resource("dynamodb",region_name=os.getenv("AWS_REGION","us-east-1"))
def _table():return _resource().Table(os.getenv("EFPS_DDB_PREFIX","efps")+"-bugs")
def _sessions():return _resource().Table(os.getenv("EFPS_DDB_PREFIX","efps")+"-sessions")
def _now():return datetime.now(timezone.utc).isoformat(timespec="seconds")
def _id():return "BUG-"+uuid.uuid4().hex[:4].upper()

def log_error(summary:str,*,where:str="",reference:str="",detail:str="",severity:str="major",reported_by:str="system",_res=None)->dict:
    table=(_res.Table(os.getenv("EFPS_DDB_PREFIX","efps")+"-bugs") if _res is not None else _table());item={"bug_id":_id(),"status":"open","summary":str(summary)[:240],"where":where,"reference":reference,"expected":"","announced":False,"severity":severity,"detail":detail[:3000],"source":"runtime","reported_by":reported_by,"reported_at":_now()};table.put_item(Item=item);return item

def all_bugs(*,_res=None):return (_res.Table(os.getenv("EFPS_DDB_PREFIX","efps")+"-bugs") if _res is not None else _table()).scan().get("Items",[])
def open_bugs(*,_res=None):return [x for x in all_bugs(_res=_res) if x.get("status")!="closed"]
def format_one(item):return f"*{item.get('bug_id')}* · {item.get('status')} · {item.get('severity')}\n{item.get('summary','')}\n_{item.get('where','')}_"
def format_list(items):return "\n\n".join(format_one(x) for x in items[:20]) or "No open bugs."
def flush_unannounced(limit=5,**_kw):return []

def _key(user):return "bugreport:"+str(user)
def in_progress(user_id,**_kw):return bool(_sessions().get_item(Key={"user_id":_key(user_id)}).get("Item"))
def start(user_id,**_kw):
    _sessions().put_item(Item={"user_id":_key(user_id),"kind":"bugreport","step":"summary","expires_at":int(datetime.now(timezone.utc).timestamp())+3600});return "Bug report started. Describe the problem in one message."
def answer(user_id,text,**_kw):
    item=_sessions().get_item(Key={"user_id":_key(user_id)}).get("Item")
    if not item:return ""
    if item.get("step")=="summary":item.update({"step":"detail","summary":str(text)[:240]});_sessions().put_item(Item=item);return "Recorded. Now describe what should have happened and any useful detail."
    item["detail"]=str(text)[:3000];_sessions().put_item(Item=item);return "Recorded. Use `/efps bug submit` to file it, or `/efps bug cancel` to discard it."
def submit(user_id,**_kw):
    item=_sessions().get_item(Key={"user_id":_key(user_id)}).get("Item")
    if not item:return "No active bug report."
    bug=log_error(item.get("summary",""),where="operator report",detail=item.get("detail",""),severity="major",reported_by=user_id);_sessions().delete_item(Key={"user_id":_key(user_id)});return f"Filed `{bug['bug_id']}`."
def cancel(user_id,**_kw):
    _sessions().delete_item(Key={"user_id":_key(user_id)});return "Bug report cancelled."
def close(bug_id,note,*,closed_by="",_res=None):
    table=(_res.Table(os.getenv("EFPS_DDB_PREFIX","efps")+"-bugs") if _res is not None else _table());items=table.scan().get("Items",[]);item=next((x for x in items if str(x.get("bug_id","")).upper()==str(bug_id).upper()),None)
    if not item:raise ValueError(f"No bug called `{bug_id}`.")
    item.update({"status":"closed","fix_note":str(note)[:1000],"closed_by":closed_by,"closed_at":_now()});table.put_item(Item=item);return item
