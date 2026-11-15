from pathlib import Path
import sys
from types import SimpleNamespace
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from shared.ola_maps.source_link import allowed, pin_coordinates, inspect_link, RestrictedRedirect, LinkEvidence
from shared.ola_maps.client import OlaMapsClient, OlaGeocodeResult


@pytest.mark.parametrize('url', [
    'http://maps.app.goo.gl/a', 'https://maps.app.goo.gl.evil.test/a',
    'https://maps.app.goo.gl@localhost/a', 'https://127.0.0.1/a',
    'https://www.google.com/search?q=x', 'https://goo.gl/anything',
    'https://www.google.com:8443/maps', 'file:///etc/passwd',
])
def test_rejects_unsupported_source_and_redirect_hosts(url):
    assert not allowed(url)
    class MustNotOpen:
        def open(self, *args, **kwargs):
            raise AssertionError('unsupported URL reached network')
    assert not inspect_link(url, opener=MustNotOpen()).reachable
    with pytest.raises(ValueError):
        RestrictedRedirect().redirect_request(None, None, 302, '', {}, url)


@pytest.mark.parametrize('url, expected', [
    ('https://www.google.com/maps/place/x/@12.9,77.6,17z', None),
    ('https://www.google.com/maps/place/x/data=!3d12.9!4d77.6', (12.9, 77.6, 'place_pin')),
    ('https://www.google.com/maps?q=12.9%2C77.6', (12.9, 77.6, 'coordinate_query')),
    ('https://www.google.com/maps?q=91,77', None),
    ('https://www.google.com/maps?q=12.9,181', None),
    ('https://www.google.com/maps/data=!3d12.9!4d77.6!3d13.1!4d77.7', None),
])
def test_camera_center_is_never_treated_as_property_pin(url, expected):
    assert pin_coordinates(url) == expected


def test_link_reachable_does_not_mean_pin_verified():
    class Reply:
        status = 200
        def geturl(self): return 'https://www.google.com/maps/place/SJR'
        def __enter__(self): return self
        def __exit__(self, *args): pass
    out = inspect_link('https://maps.app.goo.gl/test', opener=SimpleNamespace(open=lambda *a, **k: Reply()))
    assert out.reachable and out.latitude is None


@pytest.mark.parametrize('lat,lng', [(91, 1), (1, 181), (float('nan'), 1), (True, 1), ('12', 77)])
def test_invalid_coordinates_never_call_api(lat, lng):
    assert OlaMapsClient(api_key='test').reverse_geocode(lat, lng).confidence == 'INVALID_COORDINATES'


def test_reverse_geocoding_uses_existing_payload_parser(monkeypatch):
    import io, json
    payload = {'geocodingResults': [{'formatted_address': 'Bellandur, Bengaluru', 'geometry': {'location': {'lat': 12.9, 'lng': 77.6}},
        'address_components': [{'long_name': 'Bellandur', 'types': ['sublocality_level_1']}, {'long_name': '560103', 'types': ['postal_code']}]}]}
    called = []
    def open_(request, timeout):
        called.append(request)
        return io.BytesIO(json.dumps(payload).encode())
    monkeypatch.setattr('urllib.request.urlopen', open_)
    out = OlaMapsClient(api_key='not-a-real-key').reverse_geocode(12.9, 77.6)
    assert out.candidates == ('Bellandur',)
    assert out.pincode == '560103'
    assert '/reverse-geocode?' in called[0].full_url
    assert 'api_key=' not in called[0].full_url


def test_production_adapter_never_promotes_ola_candidate_to_verified():
    from shared.ola_maps.inventory import OlaInventoryMaps
    class Ola:
        def geocode(self, text): return OlaGeocodeResult(candidates=('Bellandur',), confidence='OK')
        def reverse_geocode(self, lat, lng): return OlaGeocodeResult(candidates=('Bellandur',), confidence='OK')
    adapter = OlaInventoryMaps(Ola(), link_inspector=lambda url: LinkEvidence(url, reachable=True, latitude=12.9, longitude=77.6))
    result = adapter.resolve(maps_url='source', address='SJR, Bellandur')
    assert result.confidence == 'OLA_EVIDENCE'
    assert result.locality == result.place_name == ''
    assert result.evidence['pin_status'] == 'coordinates_reverse_geocoded_not_building_verified'


def test_ola_generic_city_candidate_does_not_verify_source_locality():
    from shared.ola_maps.inventory import OlaInventoryMaps
    class Ola:
        def geocode(self, text):
            return OlaGeocodeResult(candidates=('Bengaluru', 'Kanakapura'), formatted_address='Bengaluru, Kanakapura, 560056', confidence='OK')
    result = OlaInventoryMaps(Ola(), link_inspector=lambda u: LinkEvidence(u, reachable=True)).resolve(maps_url='source', address='SJR, Bellandur, Bengaluru', expected_locality='Bellandur')
    assert result.evidence['address_status'] == 'candidate_rejected_source_locality_not_corroborated'
    assert result.locality == result.pincode == ''


def test_reverse_payload_uses_results_not_forward_geocoding_results():
    parsed = OlaMapsClient._parse({'results': [{'formatted_address':'Bellandur', 'address_components': [{'long_name':'Bellandur', 'types':['sublocality']}]}]})
    assert parsed.confidence == 'OK'
    assert parsed.candidates == ('Bellandur',)
