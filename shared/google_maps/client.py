"""Reusable Google Maps technical adapter; business decisions stay in modules."""
from __future__ import annotations
from dataclasses import dataclass
import os,re,urllib.parse,urllib.request

@dataclass(frozen=True)
class MapsResolution:
    canonical_url:str=''; formatted_address:str=''; locality:str=''; pincode:str=''; latitude:float|None=None; longitude:float|None=None; confidence:str='NOT_VERIFIED'

class GoogleMapsClient:
    API='https://maps.googleapis.com/maps/api/geocode/json'
    SHORT_HOSTS=('maps.app.goo.gl','goo.gl','maps.google.com','share.google')
    def __init__(self,api_key=None):
        self.api_key=api_key or os.getenv('GOOGLE_MAPS_API_KEY','')
        if not self.api_key:
            try:
                from shared.credentials import get_secret
                self.api_key=get_secret('efps-google-maps-api-key')
            except Exception:
                self.api_key=''
    @staticmethod
    def extract_url(text:str)->str:
        m=re.search(r'https?://(?:maps\.app\.goo\.gl|goo\.gl|www\.google\.com/maps|maps\.google\.com|share\.google)\S+',text or '',re.I);return m.group(0).rstrip('.,)') if m else ''
    @classmethod
    def expand(cls,url:str)->str:
        if not any(h in url for h in cls.SHORT_HOSTS):return url
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req,timeout=15) as r:return r.geturl() or url
        except Exception:return url
    @staticmethod
    def _query_from_url(url:str)->str:
        decoded=urllib.parse.unquote(url)
        m=re.search(r'(-?\d{1,3}\.\d{4,})[,/@\s]+(-?\d{1,3}\.\d{4,})',decoded)
        if m:return f'{m.group(1)},{m.group(2)}'
        m=re.search(r'/maps/place/([^/@?]+)',decoded)
        if m:return m.group(1).replace('+',' ')
        p=urllib.parse.urlparse(decoded);q=urllib.parse.parse_qs(p.query)
        for key in ('q','query','destination'):
            if q.get(key):return q[key][0].replace('+',' ')
        return ''
    def resolve(self,*,maps_url:str='',address:str='')->MapsResolution:
        source=maps_url.strip() or self.extract_url(address)
        if not source and not address.strip():return MapsResolution()
        if not self.api_key:return MapsResolution(canonical_url=source,confidence='NEEDS_RUNTIME_VERIFICATION')
        query=self._query_from_url(self.expand(source)) if source else address.strip()
        if not query:query=address.strip()
        params={'address':query,'key':self.api_key}
        if re.fullmatch(r'-?\d{1,3}\.\d{4,},-?\d{1,3}\.\d{4,}',query):params={'latlng':query,'key':self.api_key}
        import requests
        r=requests.get(self.API,params=params,timeout=20);r.raise_for_status();data=r.json();results=data.get('results',[])
        if not results:return MapsResolution(canonical_url=source,confidence='NOT_FOUND')
        x=results[0];comps={}
        for c in x.get('address_components',[]):
            for t in c.get('types',[]):comps.setdefault(t,c.get('long_name',''))
        g=x.get('geometry',{}).get('location',{});place=x.get('place_id','')
        locality=comps.get('sublocality_level_1') or comps.get('sublocality') or comps.get('neighborhood') or comps.get('locality','')
        canonical=f'https://www.google.com/maps/search/?api=1&query={g.get("lat")},{g.get("lng")}' + (f'&query_place_id={place}' if place else '') if g else source
        confidence='VERIFIED' if not x.get('partial_match') else 'PARTIAL_MATCH'
        return MapsResolution(canonical,x.get('formatted_address',''),locality,comps.get('postal_code',''),g.get('lat'),g.get('lng'),confidence)
    def geocode_address(self,address:str)->MapsResolution:return self.resolve(address=address)
