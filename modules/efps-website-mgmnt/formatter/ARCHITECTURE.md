# EasyFind Formatter - Version 1 Architecture

## Design Philosophy

**Lean, focused, and extensible.**

Version 1 is intentionally small. It should ship a working formatter quickly with clean separation of concerns and no extra platform layers.

---

## Core Flow

```
User Input (Raw Property Details)
    ↓
Input Validation & Sanitization
    ↓
Google Places API Resolution
    ↓
Community Type Detection
    ↓
Property Standardization
    ↓
GPT Formatting (via OpenAI)
    ↓
Formatted Output Ready for Copy-Paste
```

---

## Directory Structure

```text
formatter/
├── api/                    # HTTP handlers
├── services/               # Business logic
├── engines/                # Reserved for future core processors
├── types/                  # Type definitions
├── utils/                  # Utility helpers
├── config/                 # Configuration
├── prompts/                # AI prompts and SOP docs
├── docs/                   # Documentation
├── tests/                  # Test structure
├── README.md               # Module overview
└── index.ts                # Main barrel export
```

---

## Layer Responsibilities

### API Layer (`formatter/api/`)
- Accept HTTP requests
- Validate request format
- Handle errors gracefully
- Return standardized responses

### Services Layer (`formatter/services/`)
- `formatterEngine`: Orchestrates the full flow
- `googlePlaces`: Resolves locations via Google Places API
- `aiFormatter`: Sends data to OpenAI GPT-5.5
- `validator`: Validates property details
- `sanitizer`: Cleans input and output
- `communityDetector`: Determines gated vs semi-gated
- `standardizer`: Normalizes property fields

### Engines Layer (`formatter/engines/`)
- Reserved for future SOP engine and property parser work
- Use when logic becomes complex enough to separate from services

### Types Layer (`formatter/types/`)
- Property definitions
- API contracts
- Error types
- API integration types

### Utils Layer (`formatter/utils/`)
- Formatters: INR, dates, strings
- Parsers: Extract values from text
- Constants: Enums and config values
- Validators: Format checking
- Regex: Common patterns

### Config Layer (`formatter/config/`)
- Environment variables
- API key management
- Feature flags
- Application settings

---

## Request Flow Example

```typescript
// User sends raw property details to /api/formatter
POST /api/formatter
{
  "propertyDetails": "2BHK in Sarjapur Road, semi-furnished, 40000 rent...",
  "googleMapsUrl": "https://maps.google.com/..."
}

// 1. API validates request (api/formatter.handler.ts)
// 2. Services orchestrate flow (services/formatterEngine.ts)
//    - Validate and sanitize input
//    - Resolve Google Maps location
//    - Detect community type
//    - Standardize fields
//    - Send to GPT-5.5
// 3. Return formatted property listing

RESPONSE 200
{
  "success": true,
  "data": {
    "formatted": "Semi-furnished 2 BHK with 2 bathrooms & 1 balcony...",
    "parsed": { "bhk": 2, "rent": 40000, "...": "..." }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## Version 1 MVP

Focus on these three files:

1. `services/formatterEngine.ts` - Main orchestration
2. `services/aiFormatter.ts` - GPT integration
3. `services/googlePlaces.ts` - Location resolution

Everything else supports these core functions.

---

## Key Principles

- Lean: only what is needed for Version 1
- Focused: clear responsibilities per module
- Extensible: easy to add layers later
- Clean: simple imports and exports
- Documented: purpose of each file is clear
- Type-safe: full TypeScript throughout
- Testable: modular design enables testing

---

## Next Steps

1. Implement core services
2. Add type implementations
3. Add utility functions
4. Test the basic flow
5. Integrate Google Places API
6. Integrate OpenAI API
