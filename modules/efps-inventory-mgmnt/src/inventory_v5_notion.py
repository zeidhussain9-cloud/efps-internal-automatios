"""Schema-checked narrow page adapter. Never creates columns or pages."""
from __future__ import annotations
try:
    from .inventory_v5_adapter import read_notion_value,serialize_notion
    from .inventory_v5_http import V5NotionWriteError
    from .inventory_v5 import field_equal,content_hash
except ImportError:
    from inventory_v5_adapter import read_notion_value,serialize_notion
    from inventory_v5_http import V5NotionWriteError
    from inventory_v5 import field_equal,content_hash

class V5NotionPort:
    def __init__(self,client,schema,*,record_receipt=None):self.client=client;self.schema=schema;self.record_receipt=record_receipt

    def snapshot(self,page_id):
        page=self.client.get_page(page_id)
        row={name:read_notion_value(prop) for name,prop in page.get('properties',{}).items()
             if prop.get('type') in ('multi_select','title','rich_text','select','status','checkbox','number','date','url','email','phone_number')}
        row['_edited_at']=page.get('last_edited_time')
        row['_archived']=bool(page.get('archived') or page.get('in_trash'))
        return row

    def patch(self,page_id,values):
        properties={}
        for name,value in values.items():
            definition=self.schema.get(name)
            if not definition:raise ValueError('Missing Notion property: '+name)
            kind=definition['type']
            if kind in ('select','status','multi_select'):
                options={x['name']for x in definition[kind].get('options',[])}
                selected=value if isinstance(value,list) else [value] if value else []
                if any(x not in options for x in selected):raise ValueError('Unapproved Notion option: '+name)
            properties[name]=serialize_notion(value,kind)
        try:return self.client.update_page(page_id,properties)
        except V5NotionWriteError as error:
            binding=error.dispatch or {}
            if binding.get('page_id')!=page_id or binding.get('method')!='PATCH' or binding.get('body_hash')!=content_hash({'properties':properties}):raise
            if self.record_receipt is not None:self.record_receipt(page_id,error.receipt())
            if not error.explicitly_saved() or self.record_receipt is None:raise
            readback=self.snapshot(page_id)
            if any(not field_equal(k,readback.get(k),v)for k,v in values.items()):raise
            return {'saved_terminal_readback':True,'receipt':error.receipt()}
