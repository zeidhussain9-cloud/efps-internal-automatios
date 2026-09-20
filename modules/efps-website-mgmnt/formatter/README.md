# EasyFind Property Formatter Module

## Purpose

The EasyFind Formatter is an **internal tool** designed to transform raw property information into EasyFind's standardized property listing format. It operates as a **completely isolated feature module** independent from the main website.

**Key Characteristics**:
- ✅ Standalone module with zero dependencies on website code
- ✅ Completely isolated in `formatter/` folder
- ✅ Future: Available at `/formatter` route
- ✅ Status: **Planning Phase** (architecture only, no logic implemented)

---

## Overall Architecture

The formatter follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                   Formatter Module                      │
├─────────────────────────────────────────────────────────┤
│ UI Layer (formatter/ui/)                                 │
│ - React components for user interface                    │
│ - Form inputs, preview, copy-to-clipboard               │
├─────────────────────────────────────────────────────────┤
│ API Layer (formatter/api/)                               │
│ - HTTP request handlers                                  │
│ - Route handlers (future backend)                        │
├─────────────────────────────────────────────────────────┤
│ Services Layer (formatter/services/)                     │
│ - Business logic                                         │
│ - External API integrations                              │
│ - Formatting engine                                      │
├─────────────────────────────────────────────────────────┤
│ Data Layer (formatter/types/, formatter/utils/)          │
│ - TypeScript type definitions                            │
│ - Helper utilities and constants                         │
├─────────────────────────────────────────────────────────┤
│ AI Integration (formatter/prompts/)                      │
│ - System prompts for OpenAI                              │
│ - Formatting rules                                       │
└─────────────────────────────────────────────────────────┘
```

---

## Planned Request Flow

```
User Input
    │
    ↓
┌─────────────────────────────────────────┐
│ Paste Raw Property Details              │
│ (Address, BHK, Rent, Furnishing, etc)   │
└─────────────────────────────────────────┘
    │
    ↓
┌─────────────────────────────────────────┐
│ Formatter UI Component                  │
│ (formatter/ui/FormatterInterface.tsx)   │
└─────────────────────────────────────────┘
    │
    ↓
┌─────────────────────────────────────────┐
│ Input Validation & Parsing              │
│ (formatter/services/validator.ts)       │
└─────────────────────────────────────────┘
    │
    ↓
┌─────────────────────────────────────────┐
│ Google Places API Integration           │
│ (formatter/services/googlePlaces.ts)    │
│ - Resolve location                      │
│ - Detect society/landmark               │
└─────────────────────────────────────────┘
    │
    ↓
┌─────────────────────────────────────────┐
│ Community Type Detection                │
│ (formatter/services/communityDetector.ts)│
│ - Gated vs Semi-gated                   │
└─────────────────────────────────────────┘
    │
    ↓
┌─────────────────────────────────────────┐
│ OpenAI GPT-4 Processing                 │
│ (formatter/services/aiFormatter.ts)     │
│ (Future: GPT-5.5)                       │
│ - Apply formatting rules                │
│ - Standardize fields                    │
└─────────────────────────────────────────┘
    │
    ↓
┌─────────────────────────────────────────┐
│ Standardized Property Listing           │
│ (formatter/services/formatOutput.ts)    │
└─────────────────────────────────────────┘
    │
    ↓
┌─────────────────────────────────────────┐
│ Output Display & Copy                   │
│ (formatter/ui/PropertyOutput.tsx)       │
│ - Show formatted result                 │
│ - Copy-to-clipboard button              │
└─────────────────────────────────────────┘
```

---

## Folder Structure & Responsibilities

### `formatter/api/`
**Purpose**: HTTP request handlers and route management (future backend)

**Responsibility**:
- Define API request handlers
- Validate incoming requests
- Format API responses
- Error handling and status codes
- Route definitions (Express/Fastify)

**Key Files**:
- `formatter.handler.ts` - Main formatter endpoint handler
- `validators.ts` - Request validation middleware
- `errorHandler.ts` - Error handling

---

### `formatter/services/`
**Purpose**: Business logic and external integrations

**Responsibility**:
- Implement core formatting logic
- Integrate with external APIs (Google Places, OpenAI)
- Data validation and sanitization
- Property type detection
- Standardization rules

**Key Files**:
- `formatterEngine.ts` - Main formatting logic
- `googlePlaces.ts` - Google Places API client
- `aiFormatter.ts` - OpenAI GPT integration
- `validator.ts` - Data validation
- `sanitizer.ts` - Input/output sanitization
- `communityDetector.ts` - Detect gated/semi-gated societies
- `standardizer.ts` - Standardize property fields

---

### `formatter/ui/`
**Purpose**: React components for user interface

**Responsibility**:
- Build user-facing React components
- Handle form input and submission
- Display formatted output
- Manage UI state (loading, errors, success)
- Copy-to-clipboard functionality

**Key Files**:
- `FormatterInterface.tsx` - Main container component
- `PropertyInput.tsx` - Form for raw property details
- `PropertyOutput.tsx` - Display formatted result
- `Preview.tsx` - Live preview of formatting
- `CopyButton.tsx` - Copy-to-clipboard button

---

### `formatter/components/`
**Purpose**: Reusable UI building blocks

**Responsibility**:
- Create generic, reusable UI components
- Maintain consistent design system
- Independent from formatter logic

**Key Files**:
- `FormField.tsx` - Generic form input wrapper
- `LoadingSpinner.tsx` - Loading indicator
- `ErrorAlert.tsx` - Error message display
- `SuccessAlert.tsx` - Success message display
- `Card.tsx` - Card container component
- `Button.tsx` - Button component

---

### `formatter/types/`
**Purpose**: TypeScript type definitions

**Responsibility**:
- Define all TypeScript interfaces
- Ensure type safety across module
- Document data structures

**Key Files**:
- `property.ts` - Property listing type definitions
- `api.ts` - API request/response types
- `formatter.ts` - Formatter configuration types
- `error.ts` - Custom error types
- `google-places.ts` - Google Places API types
- `openai.ts` - OpenAI API types

---

### `formatter/utils/`
**Purpose**: Helper functions and utilities

**Responsibility**:
- Provide reusable utility functions
- Format strings, numbers, dates
- Define constants and enums
- String manipulation helpers

**Key Files**:
- `formatters.ts` - Formatting helper functions (INR, dates, etc)
- `parsers.ts` - Parsing helper functions
- `constants.ts` - Application constants
- `validators.ts` - Validation helper functions
- `regex.ts` - Regular expressions for parsing

---

### `formatter/config/`
**Purpose**: Configuration management

**Responsibility**:
- Centralize configuration values
- Manage environment-specific settings
- API key management (future)
- Feature flags

**Key Files**:
- `config.ts` - Main configuration
- `environment.ts` - Environment variables
- `features.ts` - Feature flags
- `api-config.ts` - API configuration (keys, endpoints)

---

### `formatter/prompts/`
**Purpose**: AI system prompts and formatting documentation

**Responsibility**:
- Store OpenAI system prompts
- Document formatting rules
- Maintain SOP (Standard Operating Procedure)
- Define standardization patterns

**Key Files**:
- `system-prompt.md` - OpenAI system prompt
- `formatting-rules.md` - Detailed formatting rules
- `sop.md` - Standard Operating Procedure
- `examples.json` - Example input/output pairs

---

### `formatter/docs/`
**Purpose**: Technical documentation

**Responsibility**:
- API documentation
- Integration guides
- Architecture decisions
- Development guides

**Key Files**:
- `API.md` - API endpoint documentation
- `INTEGRATION.md` - Integration guide with website
- `ARCHITECTURE.md` - Architecture decisions
- `DEVELOPMENT.md` - Development setup guide

---

### `formatter/tests/`
**Purpose**: Test files (unit, integration, E2E)

**Responsibility**:
- Unit tests for services
- Integration tests for APIs
- Component tests for UI
- E2E tests

**Key Files**:
- `unit/` - Unit test files
- `integration/` - Integration test files
- `e2e/` - End-to-end test files
- `fixtures/` - Test data and mocks

---

## Development Roadmap

### ✅ Phase 1: Structure & Planning (CURRENT)
- [x] Create isolated module structure
- [x] Create placeholder files
- [x] Document architecture
- [ ] Verify website still builds

### ⏳ Phase 2: Core Services (PENDING)
- [ ] Implement formatter engine
- [ ] Create type definitions
- [ ] Add utility functions
- [ ] Implement validators

### ⏳ Phase 3: External Integrations (PENDING)
- [ ] Integrate Google Places API
- [ ] Integrate OpenAI API
- [ ] Add error handling

### ⏳ Phase 4: UI Components (PENDING)
- [ ] Create React components
- [ ] Build formatter interface
- [ ] Add copy-to-clipboard functionality
- [ ] Implement loading states

### ⏳ Phase 5: API Layer (PENDING)
- [ ] Create API handlers
- [ ] Add request validation
- [ ] Implement error responses
- [ ] Add logging

### ⏳ Phase 6: Integration & Deployment (PENDING)
- [ ] Route: `/formatter` endpoint
- [ ] Integrate with website (optional)
- [ ] Update Render configuration (optional)
- [ ] Deploy to production

---

## Isolation Guarantee

✅ **Website Independence**: Zero impact on existing website code
- No modifications to `src/` directory
- No changes to existing routes
- No modifications to Render configuration
- No changes to `package.json` (if possible)

✅ **No Conflicts**:
- Separate namespace: `formatter/`
- Future route: `/formatter` (no collision with `/`)
- Independent dependencies

✅ **Extraction Ready**:
- Can be converted to standalone API service
- Can be deployed independently
- Can be shared across projects

---

## Development Notes

- All files are **placeholders** with TODO comments
- No actual logic implemented yet
- Ready for Phase 2: Core Services implementation
- Awaiting approval before proceeding
