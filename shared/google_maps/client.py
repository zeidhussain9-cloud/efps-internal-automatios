"""Deprecated import compatibility: source links + Ola only, no Google API.

Kept temporarily for external import compatibility. Production inventory imports
shared.ola_maps directly. Legacy api_key is intentionally ignored and never read
from environment/secrets. Remove this shim only during approved cleanup.
"""
from shared.ola_maps.links import MapsLinks
from shared.ola_maps.inventory import MapsResolution, OlaInventoryMaps


class GoogleMapsClient(MapsLinks, OlaInventoryMaps):
    def __init__(self, api_key=None, *, ola_client=None, link_inspector=None):
        kwargs = {'ola_client': ola_client}
        if link_inspector is not None:
            kwargs['link_inspector'] = link_inspector
        OlaInventoryMaps.__init__(self, **kwargs)

    def geocode_address(self, address):
        return self.resolve(address=address)
