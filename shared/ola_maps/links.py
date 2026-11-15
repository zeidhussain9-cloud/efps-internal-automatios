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
