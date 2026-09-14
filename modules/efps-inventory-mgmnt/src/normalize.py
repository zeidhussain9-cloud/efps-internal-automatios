"""Deterministic, non-inferential normalization migrated from legacy inventory."""
from __future__ import annotations
import re
from shared.google_sheets.schema import BY_NAME
FIXED={'transaction_type':'Rent','city':'Bengaluru','whatsapp_contact_link':'https://wa.me/919148338801','whatsapp_group_link':'https://chat.whatsapp.com/FxOPO0xAOsD6lNwPcIDdFM'}
NUMERIC={'pincode','built_up_area','carpet_area','age_of_property_years','total_floors','bathrooms','balconies','open_parking','monthly_rent','maintenance','security_deposit'}
SEMI=['Wardrobe','Modular Kitchen','Geyser','Fan','Light']
FULL=SEMI+['Fridge','Washing Machine','TV','Sofa','Bed','Dining Table']
PORTAL={'Triplex Villa':'Villa','Complex Villa':'Villa','Villa Complex':'Villa','Triplex':'Independent House','Builder Floor':'Independent Floor','Independent Building':'Independent House'}
NO_FLOOR={'Villa','Independent House','Farm House','Duplex'}
GATED=['Lift','Gym','CCTV','Power Backup','Swimming Pool','Gated Community','Club House','Garden','Sports','Kids Area','Community Hall']
SEMI_GATED=['CCTV','Power Backup','Regular Water Supply']
def clean(v):
    x=str(v or '').strip().replace('₹','').replace(',','')
    x=re.sub(r'\b(?:sq\.?\s*ft\.?|sqft|sft|rs\.?|inr)\b','',x,flags=re.I).strip()
    return x if re.fullmatch(r'\d+(?:\.\d+)?',x) else str(v or '').strip()
def normalize(row:dict,raw_text:str='')->dict:
    out={k:str(v or '').strip() for k,v in row.items()}
    out.update(FIXED)
    for k in NUMERIC:
        if out.get(k):out[k]=clean(out[k])
    if out.get('BHK'):
        m=re.fullmatch(r'\s*(\d+)\s*[- ]?\s*bhk\s*',out['BHK'],re.I)
        if m:out['BHK']=f'{m.group(1)} BHK'
        elif out['BHK'].lower() in ('studio','1 rk'):out['BHK']='1 RK'
    if out.get('property_subtype') in PORTAL:out['property_subtype']=PORTAL[out['property_subtype']]
    if out.get('property_subtype') in NO_FLOOR and not out.get('floor_number'):out['floor_number']=out['property_subtype']
    if not out.get('flat_furnishings'):
        if out.get('furnish_type')=='Semi Furnished':out['flat_furnishings']=', '.join(SEMI)
        elif out.get('furnish_type')=='Fully Furnished':out['flat_furnishings']=', '.join(FULL)
    if not out.get('carpet_area') and out.get('built_up_area','').isdigit():out['carpet_area']=str(int(round(int(out['built_up_area'])*.90)))
    if not out.get('servant_room'):out['servant_room']='No'
    if out.get('maintenance_included')=='Yes':out['maintenance']='0'
    if not out.get('society_amenities'):
        if out.get('internal_property_type')=='Gated Community':out['society_amenities']=', '.join(GATED)
        elif out.get('internal_property_type') in ('Semi Gated','Standalone'):out['society_amenities']=', '.join(SEMI_GATED)
    if 'utility' in raw_text.lower() or 'utilities' in raw_text.lower():
        h=out.get('property_highlights',''); out['property_highlights']=((h+' | ') if h else '')+'Utility area'
    return out
