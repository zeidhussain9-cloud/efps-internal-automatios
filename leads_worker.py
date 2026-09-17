"""Lead stream worker and dashboard entry point."""
from __future__ import annotations
import sys
from typing import Any

sys.path.insert(0, str(__file__).rsplit("/",1)[0] + "/modules/efpd-lead-mgmnt/src")

from lead_card import post_or_update
from digest import run as digest_run
from leads import TERMINAL
from db import get_lead

COSMETIC={"card_ts","updated_at"}

def _plain(image: dict) -> dict:
    out={}
    for k,v in (image or {}).items():
        if isinstance(v,dict):
            if "S" in v: out[k]=v["S"]
            elif "N" in v: out[k]=int(v["N"]) if "." not in str(v["N"]) else float(v["N"])
            elif "BOOL" in v: out[k]=v["BOOL"]
            elif "NULL" in v: out[k]=""
            else: out[k]=next(iter(v.values()))
        else: out[k]=v
    return out

def meaningful_change(old:dict,new:dict)->bool:
    return not old or any(str(old.get(k,""))!=str(new.get(k,"")) for k in (set(old)|set(new))-COSMETIC)

def handle_stream(event:dict)->dict:
    latest={}; order=[]
    for record in event.get("Records",[]):
        if record.get("eventName")=="REMOVE": continue
        image=record.get("dynamodb") or {}; new=_plain(image.get("NewImage")); old=_plain(image.get("OldImage")); phone=new.get("phone_number")
        if not phone: continue
        if phone in latest: latest[phone]["new"]=new
        else: latest[phone]={"old":old,"new":new}; order.append(phone)
    redrawn=0; skipped=0
    for phone in order:
        pair=latest[phone]
        if not meaningful_change(pair["old"],pair["new"]): skipped+=1; continue
        try:
            current=get_lead(phone) or pair["new"]
            post_or_update(current); redrawn+=1
        except Exception as exc: print(f"lead card redraw failed for {phone}: {exc!r}")
    if redrawn:
        try: digest_run()
        except Exception as exc: print(f"lead dashboard refresh failed: {exc!r}")
    return {"redrawn":redrawn,"skipped":skipped}

def lambda_handler(event:dict, context:Any=None):
    if event.get("Records"): return handle_stream(event)
    if event.get("command")=="digest": return digest_run()
    return {"ok":True,"ignored":"nothing to do"}
