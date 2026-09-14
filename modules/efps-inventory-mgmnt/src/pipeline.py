"""Phase-1 inventory pipeline: intake close -> extraction -> Maps -> validation -> AI."""
from __future__ import annotations
from shared.google_sheets import schema
from shared.google_sheets.client import GoogleSheetsClient
from shared.google_maps import GoogleMapsClient
from . import extract,normalize,validate,listing_id
FIXED={'transaction_type':'Rent','city':'Bengaluru','whatsapp_contact_link':'https://wa.me/919148338801','whatsapp_group_link':'https://chat.whatsapp.com/FxOPO0xAOsD6lNwPcIDdFM'}
def empty_row():return {name:'' for name in schema.NAMES}
def initial_row(listing_id_value,raw_text='',source_group=''):
    row=empty_row();row.update({'listing_id':listing_id_value,'status':'Raw',**FIXED,'raw_message_text':raw_text,'intake_status':'Raw','source_group':source_group});return row
def deterministic(raw_text,row=None):
    out=empty_row() if row is None else dict(row);out.update(extract.scan(raw_text));return normalize.normalize(out,raw_text)
def process_closed_session(raw_text,*,row=None,maps_client=None,ai_llm=None):
    out=deterministic(raw_text,row);issues=[];maps=maps_client or GoogleMapsClient();maps_url=out.get('google_maps_url','') or maps.extract_url(raw_text)
    if maps_url:
        resolved=maps.resolve(maps_url=maps_url)
        if resolved.confidence=='VERIFIED':out.update({'google_maps_url':resolved.canonical_url or maps_url,'locality':resolved.locality,'pincode':resolved.pincode})
        elif resolved.confidence not in ('NOT_FOUND',''):issues.append('Google Maps runtime verification required')
    out['status']='Pending';errors=validate.validate(out)
    if errors:out['status']='Needs Review';issues.extend(errors)
    if out['status']=='Pending':
        from .ai import apply
        out=apply(out,raw_text,ai_llm)
        if out.get('_ai_conflicts'):issues.extend(str(x) for x in out['_ai_conflicts']);out.pop('_ai_conflicts',None)
    out['intake_status']='Processed';return out,issues

def write_new_property(client,row):
    """Append a brand-new row. AK:AO are blank because the row is new."""
    schema.assert_writable(schema.PANEL,[k for k,v in row.items() if v and k in schema.BY_NAME])
    return client.append_rows(schema.SHEET_ID,schema.WORKSHEET_NAME,[schema.mapping_to_row(row)])

def write_phase1_update(client,row_number,row):
    """Write only panel-owned ranges A:AJ and AP:AV; never touch AK:AO."""
    left=[row[n] for n in schema.NAMES[:36]]
    right=[row[n] for n in schema.NAMES[41:]]
    client.write_range(schema.SHEET_ID,schema.WORKSHEET_NAME,schema.range_for('listing_id','cloudinary_image_urls',row_number),[left])
    client.write_range(schema.SHEET_ID,schema.WORKSHEET_NAME,schema.range_for('raw_message_text','inventory_locked',row_number),[right])

def next_listing_id(client):
    rows=client.read_range(schema.SHEET_ID,schema.WORKSHEET_NAME,'A2:A');return listing_id.generate((r[0] for r in rows if r))
