"""Schema-checked narrow page adapter. Never creates columns or pages."""
from __future__ import annotations
try:
    from .inventory_v5_adapter import read_notion_value,serialize_notion
    from .inventory_v5_http import V5NotionWriteError,effect_context
    from .inventory_v5 import field_equal,content_hash
except ImportError:
    from inventory_v5_adapter import read_notion_value,serialize_notion
    from inventory_v5_http import V5NotionWriteError,effect_context
    from inventory_v5 import field_equal,content_hash

class V5NotionPort:
    def __init__(self,client,schema,*,record_receipt=None,bind_dispatch=None,expected_parent=None):self.client=client;self.schema=schema;self.record_receipt=record_receipt;self.bind_dispatch=bind_dispatch;self.expected_parent=expected_parent

    def snapshot(self,page_id):
        page=self.client.get_page(page_id)
        if self.expected_parent is not None:
            parent=page.get('parent') or {}
            # database_id is authoritative when both database/data-source IDs
            # are present. Missing/unknown parent is not implicitly Housing.
            source=str(parent.get('database_id') or parent.get('data_source_id') or '').replace('-','').lower()
            if source!=self.expected_parent.replace('-','').lower():
                raise ValueError('Notion page is outside the expected Housing parent')
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
        import json
        # requests' JSON encoding escapes non-ASCII by default. Bound that wire
        # representation, not only the smaller canonical semantic hash payload.
        if len(json.dumps({'properties':properties}, ensure_ascii=True, allow_nan=False).encode('utf-8')) > 500000:
            raise ValueError('Notion properties payload exceeds conservative 500KB limit')
        if self.bind_dispatch is not None:
            self.bind_dispatch(page_id,{'effect_id':effect_context.get(),'method':'PATCH','page_id':page_id,'body_hash':content_hash({'properties':properties})})
        try:return self.client.update_page(page_id,properties)
        except V5NotionWriteError as error:
            binding=error.dispatch or {}
            if binding.get('effect_id')!=effect_context.get() or not binding.get('effect_id') or binding.get('page_id')!=page_id or binding.get('method')!='PATCH' or binding.get('body_hash')!=content_hash({'properties':properties}):raise
            if self.record_receipt is not None:self.record_receipt(page_id,error.receipt())
            if not error.explicitly_saved() or self.record_receipt is None or self.bind_dispatch is None:raise
            readback=self.snapshot(page_id)
            if any(not field_equal(k,readback.get(k),v)for k,v in values.items()):raise
            return {'saved_terminal_readback':True,'receipt':error.receipt()}
