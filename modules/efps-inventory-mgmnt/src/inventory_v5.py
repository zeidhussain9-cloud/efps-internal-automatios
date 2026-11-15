"""Version-five inventory rules, staged until adapters and migration pass release gates.

Pure functions only: this module never writes Notion, SQL, media or channels.
Legacy fields are protected unless provenance explicitly allows a derived update.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re

CONTRACT_VERSION = 5
SEMI_ITEMS = 'Wardrobe, Modular Kitchen, Geyser, Fan, Light'
FULL_ITEMS = SEMI_ITEMS + ', Fridge, Washing Machine, TV, Sofa, Bed, Dining Table'
STANDARD_ITEMS = 'Security, Lift, CCTV, Power Backup'
PREMIUM_ITEMS = 'Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area'
PACKAGES = {'Semi Package': SEMI_ITEMS, 'Full Package': FULL_ITEMS,
            'Standard Amenities': STANDARD_ITEMS, 'Premium Amenities': PREMIUM_ITEMS}
FURNISHINGS = {'Semi Furnished': 'Semi Package', 'Fully Furnished': 'Full Package'}
AMENITIES = {'Semi Gated': 'Standard Amenities', 'Gated Community': 'Premium Amenities', 'Standalone': ''}
BHK_OPTIONS = ('1 RK', '1 BHK', '1.5 BHK', '2 BHK', '2.5 BHK', '3 BHK', '3.5 BHK', '4 BHK', '4.5 BHK', '5 BHK')
CHANNELS = ('Meta Catalogue', 'WhatsApp Group', 'Housing.com')
AVAILABILITY = ('Available', 'On Hold', 'Rented Out')
PIPELINE = ('Needs Review', 'Processing', 'Ready to Post', 'Removed')


def text(value):
    """Do not confuse zero with missing data."""
    return '' if value is None else str(value).strip()


def decimal_value(value):
    try:
        number = Decimal(text(value))
        return number if number.is_finite() else None
    except (InvalidOperation, ValueError):
        return None


def number_text(value):
    return format(value.normalize(), 'f')


def content_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def balcony_evidence(raw):
    """Line-bound counts, explicit negative, singular mention, or unknown.

    Conflicting count/negative evidence is not resolved by position guessing.
    """
    negative = bool(re.search(r'\b(?:no|without)\s+(?:a\s+)?balcon(?:y|ies)\b', raw, re.I))
    counts = set(re.findall(r'\b(\d+)[ \t]*balcon(?:y|ies)\b', raw, re.I))
    counts.update(re.findall(r'^[ \t]*balcon(?:y|ies)[ \t]*[:=-][ \t]*(\d+)[ \t]*$', raw, re.I | re.M))
    counts = {str(int(x)) for x in counts}
    if len(counts) > 1 or (negative and counts - {'0'}):
        return None, 'Conflicting balcony evidence'
    if negative:
        return '0', ''
    if counts:
        return next(iter(counts)), ''
    return ('1', '') if re.search(r'\bbalcony\b', raw, re.I) else ('', '')


def pet_evidence(raw):
    negative = re.search(r'\bnot[ -]+pet[ -]+friendly\b|\b(?:no|without)\s+pets?\b|\b(?:pets?|animals?)\s*(?::|=|-)?\s*(?:are\s*)?(?:no|not\s*allowed|not\s*permitted|prohibited|banned)\b', raw, re.I)
    return 'No' if negative else 'Yes'


def derive_areas(built_up, carpet, explicit):
    """Return only proposed changes; derived input is never a new source anchor."""
    b, c = decimal_value(built_up), decimal_value(carpet)
    if any(v is not None and v <= 0 for v in (b, c)):
        return {}, ['Area must be positive']
    if ('built_up_area' in explicit and b is None) or ('carpet_area' in explicit and c is None):
        return {}, ['Explicit area is not a finite number']
    if {'built_up_area', 'carpet_area'} <= set(explicit):
        return ({}, ['Carpet area exceeds built-up area']) if c > b else ({}, [])
    if 'carpet_area' in explicit:
        return {'built_up_area': number_text(c + Decimal(90))}, []
    if 'built_up_area' in explicit:
        return ({}, ['Built-up area cannot yield positive carpet area']) if b <= 90 else ({'carpet_area': number_text(b - Decimal(90))}, [])
    return {}, []


def derive_deposit(months, rent):
    m, r = decimal_value(months), decimal_value(rent)
    if m is None or m <= 0:
        return '', ['Deposit months must be a positive finite number']
    if r is None or r <= 0:
        return '', ['Deposit months retained; explicit rent needed to calculate amount']
    return number_text(m * r), []


@dataclass(frozen=True)
class ChangeSet:
    patch: dict
    conflicts: tuple[str, ...]
    issues: tuple[str, ...]
    inputs_hash: str


def dependency_patch(row, changed, provenance, *, deposit_months=None, explicit_gender=None):
    """Recompute only named parents. Never silently overwrite protected children.

    provenance maps fields to origin dictionaries. A generated value can change
    only if the current value still equals its last acknowledged generated value.
    Missing provenance on a nonblank legacy field is protected.
    """
    desired, conflicts, issues = {}, [], []
    changed = set(changed)
    if 'furnish_type' in changed:
        parent = text(row.get('furnish_type'))
        if parent in FURNISHINGS:
            desired['flat_furnishings'] = FURNISHINGS[parent]
        else:
            issues.append('Unresolved furnishing type')
    if 'internal_property_type' in changed:
        parent = text(row.get('internal_property_type'))
        if parent in AMENITIES:
            desired['society_amenities'] = AMENITIES[parent]
            if parent != 'Standalone' and not text(row.get('covered_parking')):
                desired['covered_parking'] = '1'
        else:
            issues.append('Unresolved internal property type')
    if changed & {'preferred_tenant_type', 'bachelor_preference'}:
        parent = text(row.get('preferred_tenant_type'))
        if parent == 'Family Only':
            desired['bachelor_preference'] = '-'
        elif parent == 'Open For All':
            restriction = row.get('bachelor_preference') if 'bachelor_preference' in changed else explicit_gender
            if restriction not in (None, '', 'Female Only', 'Male Only'):
                issues.append('Unresolved gender restriction')
            else:
                desired['bachelor_preference'] = restriction or ''
        else:
            issues.append('Unresolved tenant type')
    if 'locality' in changed:
        for field in ('landmark','society_name'):
            old = provenance.get(field, {})
            if not text(row.get(field)) or old.get('rule') == 'locality fallback':
                desired[field] = text(row.get('locality'))
    if 'monthly_rent' in changed and deposit_months is not None:
        value, errors = derive_deposit(deposit_months, row.get('monthly_rent'))
        desired['security_deposit'] = value
        issues.extend(errors)
    if changed & {'built_up_area', 'carpet_area'}:
        explicit = {k for k in ('built_up_area', 'carpet_area') if provenance.get(k, {}).get('origin') in ('source_explicit', 'manual')}
        values, errors = derive_areas(row.get('built_up_area'), row.get('carpet_area'), explicit)
        desired.update(values)
        issues.extend(errors)
    if 'BHK' in changed and text(row.get('BHK')) not in BHK_OPTIONS:
        issues.append('Unsupported BHK; routing must be disabled')
        # Adapter must enforce this safety gate even when a stale route is manual.
    patch = {}
    for field, value in desired.items():
        current = row.get(field, '')
        if current == value or text(current) == text(value):
            continue
        evidence = provenance.get(field, {})
        origin = evidence.get('origin', 'legacy_unknown')
        generated_current = origin == 'derived' and current == evidence.get('last_generated_value')
        empty_unowned = not text(current) and origin not in ('manual', 'source_explicit')
        if generated_current or empty_unowned:
            patch[field] = value
        else:
            conflicts.append(field)
    return ChangeSet(patch, tuple(sorted(conflicts)), tuple(issues), content_hash({'row': row, 'changed': sorted(changed), 'provenance': provenance, 'deposit_months': deposit_months, 'explicit_gender': explicit_gender, 'version': CONTRACT_VERSION}))


def channel_array(value):
    if not isinstance(value, list) or any(not isinstance(x, str) or x not in CHANNELS for x in value):
        raise ValueError('Live On must be a typed array of supported channel names')
    if len(value) != len(set(value)):
        raise ValueError('Live On cannot contain duplicate channels')
    return [x for x in CHANNELS if x in value]


def renumber_plan(ordered_page_ids, current_titles):
    if len(ordered_page_ids) != len(set(ordered_page_ids)):
        raise ValueError('Duplicate page identity in reference order')
    return [{'page_id': page, 'expected_title': current_titles.get(page, ''), 'title': str(i)}
            for i, page in enumerate(ordered_page_ids, 1) if current_titles.get(page) != str(i)]
