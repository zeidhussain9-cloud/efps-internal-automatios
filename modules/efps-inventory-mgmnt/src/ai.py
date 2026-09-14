"""Optional Vertex/Gemini verification and wording-only beautification."""
from __future__ import annotations
import json, os
REVIEW_FIELDS=('BHK','property_subtype','built_up_area','carpet_area','floor_number','total_floors','bathrooms','balconies','furnish_type','flat_furnishings','covered_parking','open_parking','preferred_tenant_type','bachelor_preference','pet_friendly','monthly_rent','maintenance','maintenance_included','security_deposit','servant_room')
BEAUTIFIED=('catalog_title','property_highlights')
def _enabled(k): return os.getenv(k,'0').lower() in {'1','true','yes','on'}
def _gemini(prompt):
    import requests
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account
    from shared.google_sheets.client import GoogleSheetsCredentials
    info=GoogleSheetsCredentials.from_environment().service_account_info
    creds=service_account.Credentials.from_service_account_info(info,scopes=['https://www.googleapis.com/auth/cloud-platform']);creds.refresh(Request())
    model=os.getenv('EFPS_GEMINI_MODEL','gemini-3.1-pro-preview'); loc=os.getenv('EFPS_VERTEX_LOCATION','global'); host='aiplatform.googleapis.com' if loc=='global' else f'{loc}-aiplatform.googleapis.com'; api='v1beta1' if model.startswith('gemini-3') else 'v1'
    url=f'https://{host}/{api}/projects/{info["project_id"]}/locations/{loc}/publishers/google/models/{model}:generateContent'
    payload={'contents':[{'role':'user','parts':[{'text':prompt}]}],'systemInstruction':{'parts':[{'text':'Return only requested JSON. Never invent property facts.'}]},'generationConfig':{'temperature':0.1,'responseMimeType':'application/json','maxOutputTokens':4096}}
    r=requests.post(url,headers={'Authorization':f'Bearer {creds.token}'},json=payload,timeout=120);r.raise_for_status();parts=r.json().get('candidates',[{}])[0].get('content',{}).get('parts',[]);text=''.join(p.get('text','') for p in parts if not p.get('thought'))
    if not text: raise ValueError('Vertex returned no text')
    return text
def review(raw,row,llm=None):
    facts={k:str(row.get(k,'')) for k in REVIEW_FIELDS if str(row.get(k,'' )).strip()}
    prompt=('Compare CANONICAL FACTS to SOURCE. Return JSON {"conflicts":[{"field":"...","reason":"..."}]}. Report only clear contradictions; never missing optional fields or guesses.\nSOURCE:\n'+raw+'\nFACTS:\n'+json.dumps(facts,ensure_ascii=False))
    data=json.loads((llm or _gemini)(prompt));return [x for x in data.get('conflicts',[]) if isinstance(x,dict) and x.get('field') in REVIEW_FIELDS and str(x.get('reason','')).strip()]
def beautify(row,llm=None):
    facts={k:row.get(k,'') for k in REVIEW_FIELDS if row.get(k,'')};prompt=('Rewrite ONLY catalog_title and property_highlights using verified facts. Return exactly JSON with those two string keys. Do not add or infer facts, proximity, amenities, quality claims or unsupported numbers.\nFACTS:\n'+json.dumps(facts,ensure_ascii=False))
    data=json.loads((llm or _gemini)(prompt));out=dict(row)
    for k in BEAUTIFIED:
        if str(data.get(k,'')).strip():out[k]=' '.join(str(data[k]).split())
    return out
def apply(row,raw,llm=None):
    out=dict(row); conflicts=[]
    if _enabled('EFPS_AI_REVIEW_ENABLED'):
        try: conflicts=review(raw,out,llm)
        except Exception as exc: conflicts=[{'field':'AI','reason':f'verification failed safely: {exc}'}]
    if conflicts: out['status']='Needs Review';out['_ai_conflicts']=conflicts;return out
    if _enabled('EFPS_AI_BEAUTIFY_ENABLED'):
        try: out=beautify(out,llm)
        except Exception: pass
    return out
