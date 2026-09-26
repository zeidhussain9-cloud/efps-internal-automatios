"""Canonical Sheet -> protected CRM mirror. Full reconciliation catches direct edits/deletes."""
import hashlib,hmac,json,os,time,urllib.request
from shared.google_sheets import schema
from shared.google_sheets.client import GoogleSheetsClient

FIELDS=('listing_id','status','intake_status','internal_property_type','listing_state','onboarded_on','locality','society_name','landmark','pincode','google_maps_url','furnish_type','BHK','bathrooms','balconies','floor_number','total_floors','built_up_area','carpet_area','monthly_rent','maintenance','maintenance_included','security_deposit','preferred_tenant_type','bachelor_preference','pet_friendly','servant_room','covered_parking','open_parking','society_amenities','flat_furnishings','property_highlights','catalog_title','cloudinary_image_urls','age_of_property_years','transaction_type','property_subtype','city','posted_url','posted_at','meta_catalog_id','meta_catalog_status')

def canonical_rows(client):
    values=client.read_range(schema.SHEET_ID,schema.WORKSHEET_NAME,'A2:AT')
    rows={}
    for raw in values:
        if not raw or not str(raw[0]).strip():continue
        row=schema.row_to_mapping((list(raw)+['']*schema.GRID_WIDTH)[:schema.GRID_WIDTH]);lid=str(row['listing_id']).strip()
        if lid in rows:raise ValueError('Duplicate listing_id in Sheet; reconciliation aborted')
        rows[lid]={key:row.get(key,'') for key in FIELDS}
    return list(rows.values())

def push(rows,*,endpoint=None,secret=None,opener=None):
    endpoint=endpoint or os.environ['CRM_INVENTORY_SYNC_URL'];secret=secret or os.environ['CRM_INVENTORY_SYNC_SECRET']
    if not endpoint.startswith('https://'):raise ValueError('HTTPS required')
    if len(secret)<32:raise ValueError('Sync secret too short')
    payload=json.dumps({'rows':rows,'source':'Housing_Listings','fullReconcile':True},sort_keys=True,separators=(',',':')).encode()
    timestamp=str(int(time.time()));signature=hmac.new(secret.encode(),timestamp.encode()+b'.'+payload,hashlib.sha256).hexdigest()
    request=urllib.request.Request(endpoint,data=payload,method='POST',headers={'Content-Type':'application/json','X-EFPS-Timestamp':timestamp,'X-EFPS-Signature':signature})
    with (opener or urllib.request.urlopen)(request,timeout=45) as response:return json.loads(response.read())

def lambda_handler(event,context):
    rows=canonical_rows(GoogleSheetsClient());result=push(rows)
    print(json.dumps({'source_count':len(rows),'sync_result':result}))
    return result
