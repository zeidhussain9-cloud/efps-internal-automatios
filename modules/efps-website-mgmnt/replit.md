# EasyFind Property Solutions

## Project Overview

A production website for **EasyFind Property Solutions** — a property services company in Bangalore. The site showcases rental services, property sales, management, NRI assistance, and investment advisory. It also includes an internal **Property Formatter** tool used daily by the EasyFind team.

## Stack

- **Frontend**: React 19, TypeScript, Vite, TanStack Router, Tailwind CSS v4
- **Backend**: Express (served as Vite dev middleware in dev, standalone Node in production)
- **APIs**: Google Places / Geocoding (for location resolution), Google Forms (lead capture)
- **Deployment**: Render (`render.yaml`)

## Running Locally

```bash
npm install
npm run dev        # Dev server + API on port 5000
npm run build      # Production build to dist/
npm run start      # Production server (serves dist/ + API)
```

On Replit, the "Start application" workflow runs `npm run dev` and serves on port 5000 (bound to `0.0.0.0`), viewable in the webview preview. `GOOGLE_PLACES_API_KEY` and `GEMINI_API_KEY` are configured as Replit Secrets.

## Key URLs

| Route | Description |
|-------|-------------|
| `/` | Landing page with contact forms and testimonials |
| `/formatter` | Internal property formatter tool |
| `/api/formatter` | POST — formats raw property text |
| `/api/formatter/health` | GET — health check |

## Property Formatter

The formatter takes raw property text (WhatsApp messages, Housing/MagicBricks listings, Google Maps links) and produces a standardized EasyFind SOP-compliant listing.

**Pipeline**: Validate → Sanitize → Parse (deterministic regex) → Google Places (if Maps URL) → Community detection → Template render

**No AI required** — Version 1 uses a fully deterministic parser and template renderer.

**Required secrets** (Replit Secrets):
- `GOOGLE_PLACES_API_KEY` — for location resolution from Google Maps URLs

**Output format** (per EasyFind SOP):
```
[Furnishing] [BHK] BHK with [X] bathrooms [& Y balcony]
Rent: ₹Xk
Maintenance: ₹Xk / Included
Deposit: ₹XL
Sqft: XXXX
Floor: X/Y
Available from: Ready to Occupy / DD MMM YYYY
Preferred tenant: Family / Bachelors / Anyone
Pets: Allowed / Not allowed
Community: Gated / Semi-gated
Location: [locality]
Society Name or Landmark: [name]
Google Maps Link: [url]
---
```

## Architecture

```
formatter/
  api/            — Express handlers (formatter.handler.ts, validators, errors)
  services/       — Core pipeline (parser, templateFormatter, googlePlaces, communityDetector, sanitizer, validator, standardizer)
  types/          — TypeScript type definitions
  utils/          — Utility functions (formatters, parsers, regex, constants)
  prompts/        — SOP reference docs
server/
  app.ts          — Express app factory (shared between dev middleware and prod server)
  index.ts        — Production entry point
  vite-formatter-plugin.ts — Mounts Express as Vite dev middleware
src/
  routes/         — TanStack Router pages (index.tsx, formatter.tsx, __root.tsx)
  components/     — React UI components
```

## Deployment (Render)

The `render.yaml` configures a Node web service. Set these secrets in the Render dashboard:
- `GOOGLE_PLACES_API_KEY`

The production server (`npm run start`) serves the built `dist/` and the formatter API together.

## User Preferences

- Do NOT introduce Gemini, OpenAI, or any AI in the formatter — Version 1 is deterministic only
- Never invent property data — unknown fields stay blank
- Keep existing project structure; do not restructure or migrate
- The formatter is an internal tool; keep it minimal and functional
