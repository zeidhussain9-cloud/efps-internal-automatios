"""Generic API Gateway/Lambda webhook request primitives."""
from __future__ import annotations
import base64,json

def body_bytes(event:dict)->bytes:
    raw=event.get("body") or ""
    if event.get("isBase64Encoded"):
        return base64.b64decode(raw)
    return str(raw).encode("utf-8")

def json_body(event:dict)->dict|None:
    try:value=json.loads(body_bytes(event).decode("utf-8"))
    except (ValueError,TypeError,UnicodeDecodeError):return None
    return value if isinstance(value,dict) else None

def response(body:dict|str,status:int=200,content_type:str="application/json")->dict:
    return {"statusCode":status,"headers":{"Content-Type":content_type},"body":json.dumps(body) if isinstance(body,dict) else body}
