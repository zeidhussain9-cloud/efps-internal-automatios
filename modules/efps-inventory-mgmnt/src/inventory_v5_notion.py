"""Schema-checked narrow page adapter. Never creates columns or pages."""
from __future__ import annotations
try:
    from .inventory_v5_adapter import read_notion_value,serialize_notion
except ImportError:
    from inventory_v5_adapter import read_notion_value,serialize_notion

class V5NotionPort:
    def __init__(self,client,schema):self.client=client;self.schema=schema

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
        return self.client.update_page(page_id,properties)
