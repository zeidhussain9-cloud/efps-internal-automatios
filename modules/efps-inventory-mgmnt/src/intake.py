"""Dedicated inventory listener and explicit NEW-to-NEW property sessions."""
from __future__ import annotations
from dataclasses import dataclass,field
from datetime import datetime,timezone
from typing import Protocol,Any
from shared.whatsapp_whapi import config
from shared.whatsapp_whapi.webhook import IncomingMessage

@dataclass
class PropertySession:
    sender:str; listing_id:str=''; source_group:str=''; started_at:str=''; messages:list[dict]=field(default_factory=list); image_count:int=0
    def append(self,message:IncomingMessage|dict):
        typ=message.message_type if isinstance(message,IncomingMessage) else str(message.get('message_type',''))
        if typ.lower() in {'image','video','document','audio'}: self.image_count+=1; return
        text=message.body if isinstance(message,IncomingMessage) else str(message.get('body') or '')
        text=text.strip()
        if text:
            ts=message.timestamp if isinstance(message,IncomingMessage) else message.get('timestamp','')
            mid=message.message_id if isinstance(message,IncomingMessage) else message.get('message_id','')
            self.messages.append({'text':text,'timestamp':ts or '','message_id':mid or ''})
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

def _field(message,key,default=''):
    return getattr(message,key,default) if isinstance(message,IncomingMessage) else message.get(key,default)
def is_new_marker(text:str)->bool:return text.strip().lower()=='new'
def is_inventory_message(message:IncomingMessage|dict)->bool:
    if isinstance(message,IncomingMessage):return message.is_inventory_listener
    return (str(message.get('sender','')).strip() in config.INVENTORY_SENDER_NUMBERS and not bool(message.get('from_me')) and not str(message.get('chat_id','')).endswith('@g.us'))

def ingest(message:IncomingMessage|dict,store:SessionStore):
    """Explicit NEW opens/closes. Text is preserved; media are only counted."""
    if not is_inventory_message(message):return 'ignored',None
    sender=str(_field(message,'sender')).strip(); text=str(_field(message,'body')).strip(); current=store.get(sender)
    if is_new_marker(text):
        if current:store.delete(sender);return 'closed',current
        s=PropertySession(sender=sender,source_group=str(_field(message,'chat_id')),started_at=str(_field(message,'timestamp') or datetime.now(timezone.utc).isoformat()));store.put(s);return 'opened',s
    if not current:return 'ignored',None
    current.append(message);store.put(current);return 'collecting',current
