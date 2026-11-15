"""Reusable Ola Maps (Krutrim) technical adapter; business decisions stay in modules."""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
import urllib.parse
import urllib.request
import uuid


@dataclass(frozen=True)
class OlaGeocodeResult:
    formatted_address: str = ""
    candidates: tuple[str, ...] = ()
    pincode: str = ""
    latitude: float | None = None
    longitude: float | None = None
    confidence: str = "NOT_VERIFIED"  # OK | ZERO_RESULTS | NO_KEY | API_UNAVAILABLE


class OlaMapsClient:
    """Minimal Ola Maps geocoding adapter used for background location work.

    Client-facing links stay on Google Maps; this adapter only resolves raw
    location text into locality-like candidate names for internal matching.
    """

    API = "https://api.olamaps.io/places/v1/geocode"
    LOCALITY_TYPES = (
        "sublocality_level_1",
        "sublocality_level_2",
        "sublocality_level_3",
        "sublocality",
        "neighborhood",
        "locality",
        "postal_town",
        "administrative_area_level_3",
    )

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OLA_MAPS_API_KEY", "")
        if not self.api_key:
            try:
                from shared.credentials import get_secret

                self.api_key = get_secret("efps-ola-maps-api-key")
            except Exception:
                self.api_key = ""

    def geocode(self, text: str) -> OlaGeocodeResult:
        """Geocode free-text into locality-like candidates; never raises."""
        query = (text or "").strip()
        if not query:
            return OlaGeocodeResult(confidence="ZERO_RESULTS")
        if not self.api_key:
            return OlaGeocodeResult(confidence="NO_KEY")
        url = self.API + "?" + urllib.parse.urlencode({"address": query})
        request_id = str(uuid.uuid4())
        request = urllib.request.Request(
            url,
            headers={
                "X-API-Key": self.api_key,
                "X-Request-Id": request_id,
                "X-Correlation-Id": request_id,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            return OlaGeocodeResult(confidence="API_UNAVAILABLE")
        results = payload.get("geocodingResults") or []
        if not results:
            return OlaGeocodeResult(confidence="ZERO_RESULTS")
        best = results[0] if isinstance(results[0], dict) else {}
        components = best.get("address_components") or []
        candidates: list[str] = []
        pincode = ""
        for wanted in self.LOCALITY_TYPES:
            for component in components:
                if not isinstance(component, dict):
                    continue
                types = component.get("types") or []
                if wanted not in types:
                    continue
                name = str(
                    component.get("long_name")
                    or component.get("short_name")
                    or component.get("name")
                    or ""
                ).strip()
                if name and name not in candidates:
                    candidates.append(name)
        for component in components:
            if isinstance(component, dict) and "postal_code" in (component.get("types") or []):
                pincode = str(
                    component.get("long_name")
                    or component.get("short_name")
                    or component.get("name")
                    or ""
                ).strip()
        name = str(best.get("name") or "").strip()
        if name and name not in candidates and not name.isdigit():
            candidates.append(name)
        formatted = str(best.get("formatted_address") or "").strip()
        geometry = best.get("geometry") or {}
        location = geometry.get("location") or {}
        return OlaGeocodeResult(
            formatted_address=formatted,
            candidates=tuple(candidates),
            pincode=pincode,
            latitude=location.get("lat"),
            longitude=location.get("lng"),
            confidence="OK",
        )
