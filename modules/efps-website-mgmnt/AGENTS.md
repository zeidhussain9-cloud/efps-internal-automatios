<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

# Strict Architectural & Operational Guidelines

## 🔒 Strict File Locks (DO NOT MODIFY)
The following files represent the fully approved, optimized, and finalized core visual layout of the **EasyFind Property Solutions Website**. They must **NEVER** be modified, refactored, or touched by any coding agent or automated process unless the user explicitly and line-by-line requests changes to them:
- `/src/routes/index.tsx` (Landing page layout, copywriting, testimonials, interactive sections)
- `/src/routes/__root.tsx` (App Shell, navigation bar, footer links, brand metadata, and SEO setup)
- `/src/styles.css` (Tailwind design tokens, theme styles, animations)
- `/src/components/` (All components supporting the approved website UI)
- `/src/lib/submitLead.ts` (Formspree & Google Forms submission pipelines)

All future features, integrations, and tool additions **must** be isolated inside the `/formatter` module or additional backend service routes, leaving the main website code completely untouched.

## 🛠️ Application Modules
This repository operates two distinct applications/services:
1.  **Main Website Landing Page**: Exclusively served on the client (React + Vite) with lead delivery handled via direct Google Forms POST and Formspree proxying.
2.  **Property Formatter Engine (`/formatter`)**: A standalone TypeScript-based parser and formatted output generator. It is serviced by a server-side route `/api/formatter` running in the Express backend (`server/index.ts`).

## 🔑 Environment Secrets
The application relies on the following environment variables. Do not overwrite or lose them:
- `VITE_FORMSPREE_ID`: (Client-side) Formspree ID for lead management. If absent, fallback is Google Forms.
- `GEMINI_API_KEY`: (Server-side) Key used by `@google/generative-ai` for formatting property listings.
- `GOOGLE_PLACES_API_KEY`: (Server-side) Key used for Google Places & Geocoding API lookups.

