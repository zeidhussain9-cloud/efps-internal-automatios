"""Restricted Google Maps link expansion, independent of any geocoding API.
Only explicit pin/query coordinates count. Camera /@lat,lng views do not.
"""
from dataclasses import dataclass
import math
import re
import urllib.parse
import urllib.request

HOSTS = {'maps.app.goo.gl', 'goo.gl', 'maps.google.com', 'www.google.com', 'google.com', 'share.google'}


def allowed(url):
    try:
        p = urllib.parse.urlsplit(url)
        if p.scheme != 'https' or p.hostname not in HOSTS or p.username or p.password or p.port not in (None, 443):
            return False
        if p.hostname in {'www.google.com', 'google.com', 'goo.gl'} and not p.path.startswith('/maps'):
            return False
        return True
    except ValueError:
        return False


class RestrictedRedirect(urllib.request.HTTPRedirectHandler):
    max_redirections = 5
    max_repeats = 2
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not allowed(newurl):
            raise ValueError('Unsupported Maps redirect')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


@dataclass(frozen=True)
class LinkEvidence:
    source_url: str
    expanded_url: str = ''
    reachable: bool = False
    latitude: float | None = None
    longitude: float | None = None
    coordinate_source: str = ''
    issue: str = ''


def pin_coordinates(url):
    decoded = urllib.parse.unquote(url)
    matches = re.findall(r'!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)', decoded)
    if len(set(matches)) > 1:
        return None
    match = re.search(r'!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)', decoded)
    kind = 'place_pin'
    if match:
        pair = match.groups()
    else:
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        pair = None
        for key in ('query', 'q'):
            value = q.get(key, [''])[0]
            candidate = re.fullmatch(r'\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*', value)
            if candidate:
                pair = candidate.groups(); kind = 'coordinate_query'; break
    if not pair:
        return None
    lat, lng = map(float, pair)
    if not math.isfinite(lat) or not math.isfinite(lng) or not -90 <= lat <= 90 or not -180 <= lng <= 180:
        return None
    return lat, lng, kind


def inspect_link(url, *, opener=None):
    """No body download. Validate source and every redirect before requesting."""
    if not allowed(url):
        return LinkEvidence(url, issue='Unsupported source URL')
    try:
        client = opener or urllib.request.build_opener(RestrictedRedirect())
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with client.open(request, timeout=15) as response:
            final = response.geturl()
            if not allowed(final) or not 200 <= response.status < 300:
                return LinkEvidence(url, issue='Unsupported final URL or response')
        coordinates = pin_coordinates(final)
        if coordinates:
            lat, lng, kind = coordinates
            return LinkEvidence(url, final, True, lat, lng, kind)
        return LinkEvidence(url, final, True, issue='No explicit pin coordinates; link reachability only')
    except Exception:
        return LinkEvidence(url, issue='Source link could not be checked')
