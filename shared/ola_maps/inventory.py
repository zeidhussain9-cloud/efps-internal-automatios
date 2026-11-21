"""Inventory Maps adapter backed only by Ola, retaining source Google links."""
from dataclasses import dataclass, field
from .client import OlaMapsClient
from .source_link import inspect_link


@dataclass(frozen=True)
class MapsResolution:
    canonical_url: str = ''
    formatted_address: str = ''
    locality: str = ''
    pincode: str = ''
    latitude: float | None = None
    longitude: float | None = None
    confidence: str = 'NOT_VERIFIED'
    place_name: str = ''
    evidence: dict = field(default_factory=dict)


class OlaInventoryMaps:
    def __init__(self, ola_client=None, *, link_inspector=inspect_link):
        self.ola = ola_client or OlaMapsClient()
        self.inspect = link_inspector

    def resolve(self, *, maps_url='', address='', expected_locality=''):
        if not maps_url and not address.strip():
            return MapsResolution()
        evidence = {'link_status': 'not_supplied', 'address_status': 'not_checked', 'pin_status': 'not_verified'}
        link = self.inspect(maps_url) if maps_url else None
        if link:
            evidence['link_status'] = 'reachable' if link.reachable else 'unreachable_or_unsupported'
            evidence['link_issue'] = link.issue
            if link.reachable and link.expanded_url:
                evidence['expanded_url'] = link.expanded_url
        if link and link.reachable and link.latitude is not None:
            result = self.ola.reverse_geocode(link.latitude, link.longitude)
            if result.confidence == 'OK':
                evidence['pin_status'] = 'coordinates_reverse_geocoded_not_building_verified'
                evidence['reverse_candidates'] = list(result.candidates)
                evidence['reverse_address'] = result.formatted_address
        result = self.ola.geocode(address) if address.strip() else None
        if result:
            evidence['address_status'] = 'geocoded_candidate_not_identity_proof' if result.confidence == 'OK' else result.confidence
            evidence['forward_candidates'] = list(result.candidates)
            evidence['forward_address'] = result.formatted_address
            if result.confidence == 'OK' and expected_locality:
                matches = [v for v in result.candidates if str(v).casefold() == expected_locality.casefold()]
                evidence['address_status'] = 'locality_exactly_corroborated_not_building_verified' if matches else 'candidate_rejected_source_locality_not_corroborated'

        # Geographic candidates are not identity proof and never overwrite source.
        return MapsResolution(canonical_url=maps_url, confidence='OLA_EVIDENCE', evidence=evidence)
