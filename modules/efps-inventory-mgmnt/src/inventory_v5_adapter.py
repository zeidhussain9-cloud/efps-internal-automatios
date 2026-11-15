"""Lossless v4/v5 compatibility adapters. Importing does not enable v5 writes."""
from __future__ import annotations
from datetime import datetime
from zoneinfo import ZoneInfo
import re
try:
    from .inventory_v5 import (AMENITIES, AVAILABILITY, BHK_OPTIONS, CHANNELS, FURNISHINGS,
                               PACKAGES, PIPELINE, channel_array, text)
except ImportError:
    from inventory_v5 import (AMENITIES, AVAILABILITY, BHK_OPTIONS, CHANNELS, FURNISHINGS,
                              PACKAGES, PIPELINE, channel_array, text)

DISPLAY_ZONE = 'Asia/Calcutta'
LEGACY_FORMAT = '%A, %B %d, %Y at %I:%M:%S %p'


def read_notion_value(prop):
    kind = prop.get('type')
    value = prop.get(kind)
    if kind == 'multi_select':
        return [x['name'] for x in value or []]
    if kind in ('title', 'rich_text'):
        return ''.join(x.get('plain_text', x.get('text', {}).get('content', '')) for x in value or [])
    if kind in ('select', 'status'):
        return (value or {}).get('name', '')
    if kind == 'checkbox':
        return 'Yes' if value else 'No'
    if kind == 'number':
        return value  # None is not zero.
    if kind == 'date':
        return (value or {}).get('start')
    if kind in ('url', 'email', 'phone_number'):
        return value or ''
    raise ValueError(f'Unsupported Notion property kind: {kind}')


def serialize_notion(value, kind):
    if kind == 'multi_select':
        return {'multi_select': [{'name': x} for x in channel_array(value)]}
    if kind in ('select', 'status'):
        return {kind: {'name': text(value)} if text(value) else None}
    if kind in ('title', 'rich_text'):
        return {kind: [{'type': 'text', 'text': {'content': text(value)}}] if text(value) else []}
    if kind == 'number':
        if value in (None, ''):
            return {'number': None}
        from decimal import Decimal, InvalidOperation
        try:
            number = Decimal(str(value))
        except InvalidOperation as exc:
            raise ValueError('Invalid numeric property value') from exc
        if not number.is_finite():
            raise ValueError('Numeric property must be finite')
        return {'number': int(number) if number == number.to_integral_value() else float(number)}
    if kind == 'checkbox':
        if value not in ('Yes', 'No', True, False):
            raise ValueError('Unknown boolean cannot be silently made false')
        return {'checkbox': value in ('Yes', True)}
    if kind == 'url':
        return {'url': text(value) or None}
    raise ValueError(f'Unsupported Notion property kind: {kind}')


def parse_onboarded(value, *, legacy_timezone):
    """Explicit timezone required for legacy naive strings; never uses host locale."""
    value = text(value)
    if not value:
        raise ValueError('Missing onboarding instant')
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})', value):
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError as exc:
            raise ValueError('Invalid qualified onboarding timestamp') from exc
    else:
        try:
            dt = datetime.strptime(value, LEGACY_FORMAT)
        except ValueError as exc:
            raise ValueError('Unrecognized onboarding timestamp; review source') from exc
        # strptime parses but does not validate the supplied weekday.
        supplied = value.split(',', 1)[0]
        if supplied != dt.strftime('%A'):
            raise ValueError('Onboarding weekday/date mismatch')
    if dt.tzinfo is None:
        if not legacy_timezone:
            raise ValueError('Timezone required for naive onboarding timestamp')
        dt = dt.replace(tzinfo=ZoneInfo(legacy_timezone))
    return dt


def display_onboarded(instant, *, display_timezone):
    if instant.tzinfo is None:
        raise ValueError('Cannot display an unqualified naive instant')
    local = instant.astimezone(ZoneInfo(display_timezone))
    # Match user-facing day/month wording and lower-case am/pm without losing instant.
    return local.strftime('%A, %B ') + str(local.day) + local.strftime(', %Y at %I:%M:%S ') + local.strftime('%p').lower()


def migrate_business_values(row):
    """Deterministic candidates only, not permission to write or trust old source."""
    out = dict(row)
    tenant = text(row.get('preferred_tenant_type'))
    if tenant in ('Family', 'Family Only'):
        tenant = 'Family Only'
    gender = text(row.get('bachelor_preference'))
    if row.get('listing_id') in ('EF-2609-GJY7', 'EF-2609-DFFP', 'EF-2609-GNTE'):
        tenant, gender = 'Open For All', 'Female Only'
    elif tenant == 'Family Only':
        gender = '-'
    elif tenant == 'Open For All' and gender == 'Open for both':
        gender = ''
    out.update(preferred_tenant_type=tenant, bachelor_preference=gender)
    furnishing = text(row.get('furnish_type'))
    current_package = text(row.get('flat_furnishings'))
    if furnishing not in FURNISHINGS:
        raise ValueError('Unsupported furnishing type requires review')
    expected = FURNISHINGS[furnishing]
    if current_package not in ('', expected, PACKAGES[expected]):
        raise ValueError('Custom furnishings require reviewed disposition')
    out['flat_furnishings'] = expected
    building = text(row.get('internal_property_type'))
    if building not in AMENITIES:
        raise ValueError('Unknown internal property type')
    amenity = text(row.get('society_amenities'))
    expected = AMENITIES[building]
    approved_amenity_cases = ('EF-2609-DS5K', 'EF-2611-6JYX', 'EF-2611-97J4')
    if building == 'Standalone' and amenity in ('', '-'):
        out['society_amenities'] = ''
    elif amenity in (expected, PACKAGES.get(expected, '')) or row.get('listing_id') in approved_amenity_cases:
        out['society_amenities'] = expected
    else:
        raise ValueError('Amenity conflict requires reviewed disposition')
    if tenant not in ('Family Only', 'Open For All'):
        raise ValueError('Unsupported tenant type')
    if gender not in (('-',) if tenant == 'Family Only' else ('', 'Female Only', 'Male Only')):
        raise ValueError('Tenant/gender conflict requires review')
    if text(out.get('BHK')) not in BHK_OPTIONS:
        raise ValueError('Unsupported BHK requires review')
    return out


def status_candidate(row, *, removed_approved_ids):
    availability = text(row.get('listing_state'))
    if availability not in AVAILABILITY:
        raise ValueError('Unknown availability')
    meta = text(row.get('meta_catalog_status'))
    if meta == 'Removed':
        if row.get('listing_id') not in removed_approved_ids:
            raise ValueError('Removed-history mapping approval absent')
        stage, live = 'Removed', []
    else:
        # Do not promote content on the strength of an old stage label alone.
        stage = 'Needs Review'
        live = ['Meta Catalogue'] if meta == 'Posted' else []
    return {'Availability': availability, 'Pipeline Status': stage, 'Live On': live}


def content_readiness(row, issues, *, route_valid):
    errors = list(issues)
    if not row.get('cloudinary_image_urls'):
        errors.append('Photos missing')
    if not text(row.get('whatsapp_post')):
        errors.append('Caption missing')
    if not route_valid:
        errors.append('BHK routing invalid')
    return ('Needs Review' if errors else 'Ready to Post'), errors


def distribution_allowed(row):
    return row.get('Availability') == 'Available' and row.get('Pipeline Status') == 'Ready to Post'
