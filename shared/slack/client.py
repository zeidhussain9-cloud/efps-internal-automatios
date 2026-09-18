"""Reusable Slack transport for EFPS."""
from __future__ import annotations
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any
API_BASE=os.getenv("EFPS_SLACK_API_BASE","https://slack.com/api")
class SlackError(RuntimeError): pass
@dataclass(frozen=True)
class SlackConfig:
    bot_token:str
    @classmethod
    def from_env(cls)->"SlackConfig":
        token=os.getenv("SLACK_BOT_TOKEN","").strip()
        if token:return cls(token)
        try:
            from shared.credentials.keychain import get_secret,MissingKeychainSecret
            token=get_secret("efps-whapi-panel-slack")
            if token:return cls(token)
        except (ImportError,MissingKeychainSecret): pass
        raise SlackError("Slack bot token is not configured")
class SlackClient:
    def __init__(self,config:SlackConfig|None=None,*,timeout:float=15.0): self.config=config or SlackConfig.from_env(); self.timeout=timeout
    def call(self, method: str, payload: dict[str, Any] | None = None, http_method: str = "POST") -> dict[str, Any]:
        url = f"{API_BASE.rstrip('/')}/{method}"
        headers = {"Authorization": f"Bearer {self.config.bot_token}", "Content-Type": "application/json; charset=utf-8"}
        data = json.dumps(payload or {}).encode() if payload else None

        if http_method == "GET" and payload:
            url += "?" + urllib.parse.urlencode(payload)
            data = None

        request = urllib.request.Request(url, data=data, headers=headers, method=http_method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                response_data = json.loads(response.read().decode())
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise SlackError(f"Slack transport failed for {method}: {exc}") from exc
        if not response_data.get("ok"):
            raise SlackError(f"Slack API {method} failed: {response_data.get('error', 'unknown_error')}")
        return response_data

    def auth_test(self): return self.call("auth.test")
    def post_message(self,channel:str,text:str,*,thread_ts:str|None=None,blocks:list[dict[str,Any]]|None=None)->str:
        payload={"channel":channel,"text":text}
        if thread_ts:payload["thread_ts"]=thread_ts
        if blocks:payload["blocks"]=blocks
        return str(self.call("chat.postMessage",payload=payload)["ts"])
    def update_message(self,channel:str,ts:str,text:str,*,blocks:list[dict[str,Any]]|None=None)->None:
        payload={"channel":channel,"ts":ts,"text":text}
        if blocks:payload["blocks"]=blocks
        self.call("chat.update",payload=payload)
    def replies(self, channel: str, ts: str) -> list[dict]:
        return self.call("conversations.replies", payload={"channel": channel, "ts": ts}, http_method="GET").get("messages", [])
    def history(self,channel:str,*,limit:int=100):return list(self.call("conversations.history",payload={"channel":channel,"limit":limit}, http_method="GET").get("messages",[]))
    def files_info(self,file_id:str):return self.call("files.info",{"file":file_id})
    def download_file(self,url:str)->bytes:
        req=urllib.request.Request(url,headers={"Authorization":f"Bearer {self.config.bot_token}"})
        try:
            with urllib.request.urlopen(req,timeout=self.timeout) as response:return response.read()
        except (urllib.error.URLError,TimeoutError) as exc:raise SlackError(f"Slack file download failed: {exc}") from exc
    def conversations_info(self,channel:str):return self.call("conversations.info",{"channel":channel})
    def users_info(self,user:str):return self.call("users.info",{"user":user})
    def add_reaction(self,channel:str,timestamp:str,name:str="white_check_mark"):self.call("reactions.add",{"channel":channel,"timestamp":timestamp,"name":name})
    def pin(self,channel:str,timestamp:str):self.call("pins.add",{"channel":channel,"timestamp":timestamp})

def api_healthcheck()->bool:
    try:SlackClient().auth_test(); return True
    except SlackError:return False
