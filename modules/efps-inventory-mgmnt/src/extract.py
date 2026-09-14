"""Deterministic extraction: read only facts explicitly written in raw text."""
from __future__ import annotations
import re

def _scale(n,s=''):
    v=float(n.replace(',','')); s=(s or '').lower()
    if s=='k':v*=1000
    elif s in ('l','lakh'):v*=100000
    return str(int(v))

def scan(text:str)->dict[str,str]:
    out={}; text=text or ''
    m=(re.search(r'\b(\d+)\s*[- ]?\s*bhk\b',text,re.I) or re.search(r'\bbed\s*rooms?\s*[:\-]\s*(\d+)\b',text,re.I) or re.search(r'\b(\d+)\s*[- ]?\s*bed\s*rooms?\b',text,re.I))
    if m: out['BHK']=f'{m.group(1)} BHK'
    elif re.search(r'\bstudio\b',text,re.I): out['property_subtype']='Studio'
    m=re.search(r'(?:rent|rental)\D{0,12}?(?:rs\.?|inr|₹)?\s*(\d[\d,]*\.?\d*)\s*(k|lakh|l)?\b',text,re.I) or re.search(r'(?:rs\.?|inr|₹)\s*(\d[\d,]*)\s*(k)?\b',text,re.I)
    if m:
        v=_scale(m.group(1),m.group(2) if m.lastindex and m.lastindex>1 else '')
        if 3000<=int(v)<=100000000:out['monthly_rent']=v
    for key,pat in [('carpet_area',r'carpet\s*area\D{0,5}(\d{3,5})'),('built_up_area',r'built-?up\s*area\D{0,5}(\d{3,5})')]:
        m=re.search(pat,text,re.I)
        if m:out[key]=m.group(1)
    if 'built_up_area' not in out:
        m=re.search(r'sqft\s*:\s*(\d{3,5})',text,re.I) or re.search(r'\b(\d{3,5})\s*(?:sq\.?\s*ft|sqft|sft)\b',text,re.I)
        if m:out['built_up_area']=m.group(1)
    m=re.search(r'floor\s*:\s*(\d{1,2})\s*(?:/|of)\s*(\d{1,2})',text,re.I)
    if m:out['floor_number'],out['total_floors']=m.group(1),m.group(2)
    else:
        m=re.search(r'\b(\d{1,2})\s*(?:st|nd|rd|th)?\s*floor\b',text,re.I)
        if m:
            out['floor_number']=m.group(1); tail=text[m.end():m.end()+25]; n=re.search(r'(?:out of|of|/)\s*(\d{1,2})',tail,re.I)
            if n:out['total_floors']=n.group(1)
    patterns={'bathrooms':r'\b(\d)\s*(?:bath|bathroom|toilet|washroom)s?\b','balconies':r'\b(\d)\s*balcon(?:y|ies)\b','maintenance':r'(?:maintenance|maint)\D{0,12}?(\d[\d,]*\.?\d*)\s*(k)?\b','covered_parking':r'(\d)\s*covered\s*parking','open_parking':r'(\d)\s*open\s*parking'}
    for k,p in patterns.items():
        m=re.search(p,text,re.I)
        if m:out[k]=_scale(m.group(1),m.group(2)) if k=='maintenance' else m.group(1)
    m=re.search(r'preferred\s*tenant\s*:\s*([^\n]+)',text,re.I)
    if m:out['preferred_tenant_type']=m.group(1).strip()
    m=re.search(r'bachelor(?:s)?\s*:\s*([^\n]+)',text,re.I)
    if m:out['bachelor_preference']=m.group(1).strip()
    m=re.search(r'pets?\s*:\s*([^\n]+)',text,re.I)
    if m:out['pet_friendly']=m.group(1).strip()
    m=re.search(r'servant\s*room\s*:\s*([^\n]+)',text,re.I)
    if m:out['servant_room']=m.group(1).strip()
    if re.search(r'maintenance\s*:\s*included\b',text,re.I):out['maintenance_included']='Yes'
    m=re.search(r'(?:deposit|dep|advance)\D{0,12}?(\d[\d,]*\.?\d*)\s*(k|lakh|l|months?|mnths?)?',text,re.I)
    if m:
        unit=(m.group(2) or '').lower()
        out['security_deposit']=str(int(float(m.group(1).replace(',',''))*int(out['monthly_rent']))) if unit.startswith(('month','mnth')) and out.get('monthly_rent','').isdigit() else _scale(m.group(1),m.group(2))
    for pat,label in [(r'\bfully\s*furnish','Fully Furnished'),(r'\bsemi[-\s]*furnish','Semi Furnished'),(r'\bun[-\s]*furnish|\bnot\s*furnish|\bempty\b','Unfurnished')]:
        if re.search(pat,text,re.I):out['furnish_type']=label;break
    return out
