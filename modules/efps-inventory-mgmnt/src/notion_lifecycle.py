"""Canonical Notion lifecycle, separate from the unchanged extraction scratch format.

Old Housing columns remain untouched. No publication or channel presence is inferred.
"""
AVAILABILITY = ('Available', 'On Hold', 'Rented Out')
PIPELINE = ('Needs Review', 'Processing', 'Ready To Post', 'Posted', 'Removed')
CHANNELS = ('Meta Catalogue', 'WhatsApp Group', 'Housing.com')
LEGACY_STATUS_FIELDS = {'status', 'intake_status', 'listing_state', 'meta_catalog_status'}
CANONICAL_FIELDS = ('Availability', 'Pipeline Status', 'live at')


def finish_processing(processed, previous=None):
    """Route the parser result without reading legacy Housing lifecycle values."""
    previous = previous or {}
    availability = previous.get('Availability', 'Available')
    if availability not in AVAILABILITY:
        raise ValueError('Existing Housing Availability is missing or invalid; not guessing')
    prior_stage = previous.get('Pipeline Status', '')
    if previous and prior_stage not in PIPELINE:
        raise ValueError('Existing Housing Pipeline Status is missing or invalid; not guessing')
    channels = previous.get('live at', [])
    if not isinstance(channels, list) or any(x not in CHANNELS for x in channels):
        raise ValueError('Existing Housing live at is invalid; not guessing')
    if processed.get('status') == 'Needs Review':
        stage = 'Needs Review'
    elif prior_stage in {'Posted', 'Removed'}:
        stage = prior_stage
    else:
        stage = 'Ready To Post'
    return {'Availability': availability, 'Pipeline Status': stage, 'live at': list(channels)}
