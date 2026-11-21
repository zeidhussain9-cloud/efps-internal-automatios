"""Source Google Maps link syntax only. No API client or credentials."""
import re
from .source_link import allowed


class MapsLinks:
    MAP_URL_RE = re.compile(r'https?://(?:maps\.app\.goo\.gl|goo\.gl|www\.google\.com/maps|maps\.google\.com|share\.google)[^<>\s|]+', re.I)

    @staticmethod
    def normalize_source_link(value):
        normalized = (value or '').strip()
        if normalized.startswith('<') and '|' in normalized:
            normalized = normalized[1:].split('|', 1)[0]
        return normalized.strip('<>\"\'*').rstrip('.,);]}*')

    @classmethod
    def extract_url(cls, text):
        for match in cls.MAP_URL_RE.finditer(text or ''):
            candidate = cls.normalize_source_link(match.group(0))
            if allowed(candidate):
                return candidate
        return ''

    @classmethod
    def is_maps_url(cls, value):
        normalized = cls.normalize_source_link(value)
        return bool(cls.MAP_URL_RE.fullmatch(normalized)) and allowed(normalized)

    @staticmethod
    def standard_search_url(value):
        """Canonical caption link: one google.com/maps/search URL for any supported Maps link.

        Every expanded short link (and any already-long source link) reduces to
        https://www.google.com/maps/search/?api=1&query=<place or coordinates>,
        so a caption never carries a short goo.gl/share.google URL. Camera
        viewport suffixes (/@lat,lng,z) are dropped; the place identity is kept.
        Returns '' when no usable place or coordinate query exists.
        """
        import urllib.parse
        normalized = (value or '').strip()
        if not normalized or not allowed(normalized):
            return ''
        parts = urllib.parse.urlsplit(normalized)
        path = parts.path or ''
        query = ''
        if '/maps/search/' in path:
            query = urllib.parse.parse_qs(parts.query).get('query', [''])[0]
        elif '/maps/place/' in path:
            segment = path.split('/place/', 1)[1]
            segment = segment.split('/data', 1)[0].split('/@', 1)[0]
            query = urllib.parse.unquote(segment).replace('+', ' ')
        else:
            params = urllib.parse.parse_qs(parts.query)
            for key in ('query', 'q'):
                raw = params.get(key, [''])[0]
                if raw:
                    query = raw.split('/@', 1)[0]
                    break
        query = ' '.join(str(query or '').split()).strip(',')
        if not query:
            return ''
        return 'https://www.google.com/maps/search/?api=1&query=' + urllib.parse.quote_plus(query, safe=',')
