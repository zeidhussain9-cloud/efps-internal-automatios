# Plan: East Bangalore Clusters Section

## What "map the clusters" means

Instead of listing localities as one flat footer list, we group East Bangalore into logical "clusters" based on geography, employment corridors, and lifestyle character. Each cluster gets a name, a short description of what it is known for, and the localities inside it. This turns a plain directory into a curated area guide that feels premium and helps visitors quickly understand where you operate.

Example cluster idea:

```text
Whitefield & ITPL Corridor
  Whitefield | ITPL | Hoodi | Mahadevapura
  Known for: IT parks, villa communities, rental demand from tech workforce.
```

## Goal

Add a new "Areas We Cover" section to the landing page that presents East Bangalore as an editorial Bento Grid of locality clusters. The section must look premium, be responsive, and use only confirmed or clearly marked placeholder data.

## Proposed clusters

1. **Whitefield & ITPL Corridor**
   - Localities: Whitefield, ITPL, Hoodi, Mahadevapura
2. **ORR Tech Belt**
   - Localities: Marathahalli, Kadubeesanahalli, Bellandur
3. **Sarjapur Road Corridor**
   - Localities: Sarjapur Road, Kasavanahalli, Harlur, Varthur
4. **Indiranagar & Old Airport Road**
   - Localities: Indiranagar, Old Airport Road
5. **Central Bangalore Hubs** (retained from existing service areas)
   - Localities: Koramangala, HSR Layout

Cluster names, descriptions, and included localities are placeholders until you confirm them.

## Section design

- Position: insert between "How It Works" and "Why Choose Us" sections.
- Layout: responsive Bento Grid using the existing navy/gold/white brand tokens.
- Each cluster card contains:
  - Cluster name (heading)
  - One-line character description (e.g., "IT corridor, villa communities, rental demand")
  - List of localities as chips or a compact inline list
  - Optional icon (MapPin / Building / Layers)
  - Clear "To be confirmed" placeholders for rent scenarios, demand profile, and broker feedback
- No numeric rent ranges, yield percentages, demand scores, or market benchmarks will be invented.

## Data rules

- All rent, yield, demand, and appreciation claims will be removed or replaced with "To be confirmed" placeholders.
- Only user-provided data will be shown as fact.
- The existing footer "Service Areas" list will be preserved and kept consistent with the cluster localities.

## Technical approach

- Add a new `AreasSection` component inside `src/routes/index.tsx`.
- Define a `CLUSTERS` data array with `name`, `tagline`, `localities`, and `note` fields.
- Render with a responsive grid: single column on mobile, 2 columns on tablet, 3–4 columns on desktop.
- Use existing Tailwind tokens and brand colors (`NAVY`, `GOLD`, `SURFACE`, `BORDER`).
- Keep the component self-contained; do not modify locked files beyond `index.tsx` for this page-level addition.

## Verification

- `bun run build` passes.
- `bunx eslint src/routes/index.tsx` passes.
- Playwright screenshots at desktop, tablet, and mobile show clean layout with no overlap.
- No console errors or warnings.
