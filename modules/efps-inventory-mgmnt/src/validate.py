"""Canonical deterministic validation for the Phase-1 inventory row."""
from __future__ import annotations
import re
from shared.google_sheets import schema
FIXED={'transaction_type':'Rent','city':'Bengaluru','whatsapp_contact_link':'https://wa.me/919148338801','whatsapp_group_link':'https://chat.whatsapp.com/FxOPO0xAOsD6lNwPcIDdFM'}
PROPERTY_SUBTYPES={'Apartment','Independent House','Duplex','Independent Floor','Villa','Penthouse','Studio','Farm House'}
FURNISH={'Fully Furnished','Semi Furnished','Unfurnished'}
COVERED={'0','1','2','3','3+'}
FURNISHINGS={'AC','Wardrobe','Geyser','Fan','Light','Fridge','TV','Bed','Sofa','Dining Table','Washing Machine','Cupboard','Microwave','Stove','Water Purifier','Gas Pipeline','Chimney','Modular Kitchen'}
AMENITIES={'Semi Gated','Standalone','Lift','Gym','CCTV','Power Backup','Swimming Pool','Gated Community','Club House','Garden','Intercom','Sports','Kids Area','Community Hall','Regular Water Supply','Attached Balcony'}
NUMERIC={'pincode','built_up_area','carpet_area','age_of_property_years','total_floors','bathrooms','balconies','open_parking','monthly_rent','maintenance','security_deposit'}

def validate(row:dict)->list[str]:
    e=[]
    if set(row)!=set(schema.NAMES):
        e.append('row shape does not match canonical 48 fields'); return e
    for k,v in FIXED.items():
        if row[k]!=v:e.append(f'{k} must be {v}')
    if row['status'] not in ('Pending','Needs Review'):e.append('status must be Pending or Needs Review after extraction')
    if not row['listing_id']:e.append('listing_id required')
    if not row['monthly_rent']:e.append('monthly_rent required')
    if row['BHK'] and not re.fullmatch(r'\d+ BHK',row['BHK']) and row['BHK']!='1 RK':e.append('invalid BHK')
    if row['property_subtype'] and row['property_subtype'] not in PROPERTY_SUBTYPES:e.append('invalid property_subtype')
    if row['furnish_type'] and row['furnish_type'] not in FURNISH:e.append('invalid furnish_type')
    for k in NUMERIC:
        if row[k] and not re.fullmatch(r'\d+(?:\.\d+)?',str(row[k])):e.append(f'{k} must be numeric')
    if row['covered_parking'] not in COVERED|{''}:e.append('invalid covered_parking')
    for k,allowed in [('flat_furnishings',FURNISHINGS),('society_amenities',AMENITIES)]:
        bad=[x.strip() for x in str(row[k]).split(',') if x.strip() and x.strip() not in allowed]
        if bad:e.append(f'{k} invalid values: {bad}')
    if row['maintenance_included'] not in ('Yes','No',''):e.append('maintenance_included must be Yes/No/blank')
    if row['maintenance_included']=='Yes' and row['maintenance']!='0':e.append('maintenance must be 0 when included')
    for k in ('posted_url','posted_at','error_notes','meta_catalog_id','meta_catalog_status'):
        if row[k]:e.append(f'{k} must remain empty before downstream stages')
    return e

def validate_raw(row:dict)->list[str]:
    e=[]
    if set(row)!=set(schema.NAMES):e.append('raw row shape does not match canonical 48 fields');return e
    if row['status']!='Raw':e.append('initial row status must be Raw')
    if not row['listing_id']:e.append('listing_id required')
    for k,v in FIXED.items():
        if row[k]!=v:e.append(f'{k} must be {v}')
    for k in ('posted_url','posted_at','error_notes','meta_catalog_id','meta_catalog_status'):
        if row[k]:e.append(f'{k} must be empty at intake')
    return e
