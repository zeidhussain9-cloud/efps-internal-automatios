"""Reusable Google Maps technical adapter; business decisions stay in modules."""
from __future__ import annotations
from dataclasses import dataclass
import os
import re
import urllib.parse
import urllib.request


@dataclass(frozen=True)
class MapsResolution:
    canonical_url: str = ""
    formatted_address: str = ""
    locality: str = ""
    pincode: str = ""
    latitude: float | None = None
    longitude: float | None = None
    confidence: str = "NOT_VERIFIED"
    place_name: str = ""


class GoogleMapsClient:
    API = "https://maps.googleapis.com/maps/api/geocode/json"
    SHORT_HOSTS = ("maps.app.goo.gl", "goo.gl", "maps.google.com", "share.google")
    MAP_URL_RE = re.compile(
        r"https?://(?:maps\.app\.goo\.gl|goo\.gl|www\.google\.com/maps|maps\.google\.com|share\.google)[^<>\s|]+",
        re.I,
    )

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY", "")
        if not self.api_key:
            try:
                from shared.credentials import get_secret
                self.api_key = get_secret("efps-google-maps-api-key")
            except Exception:
                self.api_key = ""

    @classmethod
    def normalize_source_link(cls, value: str) -> str:
        """Return the URL portion of a plain or Slack-wrapped source link."""
        normalized = (value or "").strip()
        if normalized.startswith("<") and "|" in normalized:
            normalized = normalized[1:].split("|", 1)[0]
        return normalized.strip("<>\"'*").rstrip(".,);]}*")

    @classmethod
    def extract_url(cls, text: str) -> str:
        """Extract the exact supported Maps URL from source text without network access."""
        match = cls.MAP_URL_RE.search(text or "")
        if not match:
            return ""
        return cls.normalize_source_link(match.group(0))

    @classmethod
    def is_maps_url(cls, value: str) -> bool:
        return bool(cls.MAP_URL_RE.fullmatch(cls.normalize_source_link(value)))

    @classmethod
    def expand(cls, url: str) -> str:
        if not any(h in url for h in cls.SHORT_HOSTS):
            return url
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as response:
                return response.geturl() or url
        except Exception:
            return url

    @staticmethod
    def _query_from_url(url: str) -> str:
        decoded = urllib.parse.unquote(url)
        match = re.search(r"(-?\d{1,3}\.\d{4,})[,/@\s]+(-?\d{1,3}\.\d{4,})", decoded)
        if match:
            return f"{match.group(1)},{match.group(2)}"
        match = re.search(r"/maps/place/([^/@?]+)", decoded)
        if match:
            return match.group(1).replace("+", " ")
        parsed = urllib.parse.urlparse(decoded)
        query = urllib.parse.parse_qs(parsed.query)
        for key in ("q", "query", "destination"):
            if query.get(key):
                return query[key][0].replace("+", " ")
        return ""

    def resolve(self, *, maps_url: str = "", address: str = "") -> MapsResolution:
        source = self.normalize_source_link(maps_url) or self.extract_url(address)
        if not source and not address.strip():
            return MapsResolution()
        if not self.api_key:
            return MapsResolution(canonical_url=source, confidence="NEEDS_RUNTIME_VERIFICATION")
        query = self._query_from_url(self.expand(source)) if source else address.strip()
        if not query:
            query = address.strip()
        if not query:
            return MapsResolution(canonical_url=source, confidence="NOT_FOUND")
        params = {"address": query, "key": self.api_key}
        if re.fullmatch(r"-?\d{1,3}\.\d{4,},-?\d{1,3}\.\d{4,}", query):
            params = {"latlng": query, "key": self.api_key}
        import requests
        response = requests.get(self.API, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        if not results:
            return MapsResolution(canonical_url=source, confidence="NOT_FOUND")
        result = results[0]
        components = {}
        for component in result.get("address_components", []):
            for component_type in component.get("types", []):
                components.setdefault(component_type, component.get("long_name", ""))
        geometry = result.get("geometry", {}).get("location", {})
        place = result.get("place_id", "")
        locality = (
            components.get("sublocality_level_1")
            or components.get("sublocality")
            or components.get("neighborhood")
            or components.get("locality", "")
        )
        canonical = (
            f'https://www.google.com/maps/search/?api=1&query={geometry.get("lat")},{geometry.get("lng")}'
            + (f"&query_place_id={place}" if place else "")
            if geometry
            else source
        )
        confidence = "VERIFIED" if not result.get("partial_match") else "PARTIAL_MATCH"
        return MapsResolution(
            canonical_url=canonical,
            formatted_address=result.get("formatted_address", ""),
            locality=locality,
            pincode=components.get("postal_code", ""),
            latitude=geometry.get("lat"),
            longitude=geometry.get("lng"),
            confidence=confidence,
            place_name=str(result.get("name", "") or "").strip(),
        )

    def geocode_address(self, address: str) -> MapsResolution:
        return self.resolve(address=address)
