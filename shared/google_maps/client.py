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


class GoogleMapsClient:
    API = "https://maps.googleapis.com/maps/api/geocode/json"
    SHORT_HOSTS = ("maps.app.goo.gl", "goo.gl", "maps.google.com", "share.google")
    MAP_URL_RE = re.compile(
        r"https?://(?:maps\.app\.goo\.gl|goo\.gl|www\.google\.com/maps|maps\.google\.com|share\.google)\S+",
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
    def extract_url(cls, text: str) -> str:
        """Extract the exact supported Maps URL from source text.

        This is intentionally network-free. URL recognition is a deterministic
        source operation; expansion/resolution belongs to the runtime layer.
        The returned value is normalized only for source-message wrappers and
        terminal punctuation; the URL itself is otherwise preserved exactly.
        """
        match = cls.MAP_URL_RE.search(text or "")
        if not match:
            return ""
        return match.group(0).strip("<>\"'").rstrip(".,);]}")

    @classmethod
    def is_maps_url(cls, value: str) -> bool:
        """Return whether a value is exactly one supported Maps URL."""
        return bool(cls.MAP_URL_RE.fullmatch((value or "").strip().strip("<>\"'")))

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
        source = maps_url.strip() or self.extract_url(address)
        if not source and not address.strip():
            return MapsResolution()
        if not self.api_key:
            return MapsResolution(canonical_url=source, confidence="NEEDS_RUNTIME_VERIFICATION")
        query = self._query_from_url(self.expand(source)) if source else address.strip()
        if not query:
            query = address.strip()
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
            canonical,
            result.get("formatted_address", ""),
            locality,
            components.get("postal_code", ""),
            geometry.get("lat"),
            geometry.get("lng"),
            confidence,
        )

    def geocode_address(self, address: str) -> MapsResolution:
        return self.resolve(address=address)
