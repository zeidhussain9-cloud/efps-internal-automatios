# API Documentation - EasyFind Formatter

## Status
🚧 **PLACEHOLDER** - To be implemented in Phase 5

## Purpose
This document describes the API endpoints for the formatter module.

## Future Endpoints

### POST /api/formatter
Format raw property details into standardized listing.

**Request Body:**
```json
{
  "propertyDetails": "2BHK in Sarjapur Road, semi-furnished, 40000 rent...",
  "googleMapsUrl": "https://maps.google.com/..."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "formatted": "Semi-furnished 2 BHK with 2 bathrooms...",
    "parsed": { "bhk": 2, "rent": 40000, ... }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## TODO
- [ ] Define all endpoints
- [ ] Document request/response formats
- [ ] Document error codes
- [ ] Add authentication (if needed)
- [ ] Add rate limiting documentation
- [ ] Add examples for each endpoint
