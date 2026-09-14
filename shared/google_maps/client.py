"""Small, dependency-light Google Maps/Geocoding adapter.

Business decisions stay in modules. This layer only resolves a supplied Maps URL
or address into deterministic technical location data.
"""
from __future__ import annotations
from dataclasses import dataclass
import os, re
from urllib.parse import quote, urlparse

@dataclass(frozen=True)
class MapsResolution:
    canonical_url: str = ""
    formatted_address: str = ""
    locality: str = ""
    pincode: str = ""
    latitude: float | None = None
    longitude: float | None = None
    confidence: str = "NOT_VERIFIED"

class GoogleMapsClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY", "")

    @staticmethod
    def extract_url(text: str) -> str:
        m = re.search(r"https?://(?:maps\.app\.goo\.gl|www\.google\.com/maps|maps\.google\.com)[^\s<>]+", text or "", re.I)
        return m.group(0).rstrip(".,)") if m else ""

    def resolve(self, *, maps_url: str = "", address: str = "") -> MapsResolution:
        url = maps_url.strip() or self.extract_url(address)
        if not url and not address.strip(): return MapsResolution()
        if not self.api_key:
            return MapsResolution(canonical_url=url, confidence="NEEDS_RUNTIME_VERIFICATION")
        import requests
        query = url if url else address.strip()
        r = requests.get("https://maps.googleapis.com/maps/api/geocode/json", params={"address": query, "key": self.api_key}, timeout=20)
        r.raise_for_status(); data=r.json()
        results=data.get("results",[])
        if not results: return MapsResolution(canonical_url=url, confidence="NOT_FOUND")
        x=results[0]; comps={}
        for c in x.get("address_components",[]):
            for t in c.get("types",[]): comps[t]=c.get("long_name","")
        loc=comps.get("locality") or comps.get("sublocality_level_1") or comps.get("administrative_area_level_2","")
        pin=comps.get("postal_code","")
        g=x.get("geometry",{}).get("location",{})
        lat,lon=g.get("lat"),g.get("lng")
        place_id=x.get("place_id","")
        canonical=f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else url
        return MapsResolution(canonical, x.get("formatted_address",""), loc, pin, lat, lon, "VERIFIED")

    def geocode_address(self, address: str) -> MapsResolution:
        return self.resolve(address=address)
