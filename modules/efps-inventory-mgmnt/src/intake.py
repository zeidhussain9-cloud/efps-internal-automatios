"""Dedicated inventory listener and explicit NEW-to-NEW property sessions."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol
from shared.whatsapp_whapi.webhook import is_inventory_listener

@dataclass
class PropertySession:
    sender:str; listing_id:str=''; source_group:str=''; started_at:str=''; messages:list[dict]=field(default_factory=list); image_count:int=0
    def append(self,message):
        if message.get('message_type','').lower() in {'image','video','document','audio'}: self.image_count+=1; return
        text=str(message.get('body') or '').strip()
        if text:self.messages.append({'text':text,'timestamp':message.get('timestamp',''),'message_id':message.get('message_id','')})
    @property
    def raw_text(self):
        return '\n'.join(f"[{m['timestamp']}] [{m['message_id']}] {m['text']}".strip() for m in self.messages)

class SessionStore(Protocol):
    def get(self,sender:str)->PropertySession|None: ...
    def put(self,session:PropertySession)->None: ...
    def delete(self,sender:str)->None: ...

class InMemorySessionStore:
    def __init__(self):self._data={}
    def get(self,sender):return self._data.get(sender)
    def put(self,session):self._data[session.sender]=session
    def delete(self,sender):self._data.pop(sender,None)

def is_new_marker(text:str)->bool:return text.strip().lower()=='new'

def ingest(message:dict,store:SessionStore):
    """Return ('opened'|'collecting'|'closed'|'ignored', session).

    The caller supplies the immutable listing ID when a NEW closes a property.
    Media are counted but never downloaded in Phase 1.
    """
    if not is_inventory_listener(message): return 'ignored',None
    sender=str(message.get('sender','')).strip(); text=str(message.get('body') or '').strip()
    current=store.get(sender)
    if is_new_marker(text):
        if current:
            store.delete(sender); return 'closed',current
        s=PropertySession(sender=sender,started_at=str(message.get('timestamp') or datetime.now(timezone.utc).isoformat()));store.put(s);return 'opened',s
    if not current:return 'ignored',None
    current.append(message);store.put(current);return 'collecting',current
