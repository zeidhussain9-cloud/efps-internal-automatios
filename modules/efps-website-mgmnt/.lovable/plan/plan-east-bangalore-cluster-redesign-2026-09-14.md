# Plan: East Bangalore Cluster Redesign

## Goal

Rebuild the “Areas We Cover” section as the selected premium Bento direction: six balanced cluster cards, ORR Tech Belt first and visually primary, but smaller and lighter than the prototype so it stays in sync with the EasyFind website.

## Content structure

Use only the already confirmed service areas and reorganize them into six clusters:

1. **ORR Tech Belt** — Marathahalli, Kadubeesanahalli, Bellandur
2. **Whitefield & ITPL Corridor** — Whitefield, ITPL
3. **Hoodi & Mahadevapura** — Hoodi, Mahadevapura
4. **Sarjapur Road Corridor** — Sarjapur Road, Kasavanahalli, Harlur, Varthur
5. **Indiranagar & Old Airport Road** — Indiranagar, Old Airport Road
6. **Central Bangalore Hubs** — Koramangala, HSR Layout

Descriptions will stay geographic and service-oriented. Unconfirmed market information remains clearly marked “To be confirmed”; no property counts, rents, yields, demand ratings, or listing claims will be added.

## Visual direction

- Use the selected mixed surfaces: navy, pale blue-grey, soft warm neutral, and white.
- Apply Libre Baskerville to section/card headings and IBM Plex Sans to supporting text.
- Give ORR the first and largest position, but limit it to a compact rectangular anchor rather than the oversized dark square shown in the prototype.
- Use a lighter navy treatment and soft glass-like borders/shadows so ORR feels integrated with the existing website.
- Give each cluster a distinct, relevant icon and subtle surface treatment.
- Complete the grid with six cards so no empty desktop space remains.
- Keep the layout single-column on mobile and balanced across tablet and desktop.

## Interaction and trust

- Restyle locality names as clearly static labels, not controls.
- Add a **Call about this area** action to every card using the existing phone destination without displaying the number.
- Include the cluster name in the accessible call label so each action is unambiguous.
- Use restrained lift/arrow feedback and respect reduced-motion preferences.

## Technical scope

- Update only the existing Areas section and its cluster data in `src/routes/index.tsx`.
- Add the selected font loading in `index.html` without changing the approved global design system.
- Preserve the footer service-area list, contact details, forms, navigation, and all other sections.

## Verification

- Run formatting, targeted linting, TypeScript/build checks, and inspect the latest build diagnostics.
- Verify the section at desktop, tablet, and mobile widths.
- Confirm six cards render, ORR is first, the grid has no empty hole, all call actions use the correct destination, static labels do not imply filtering, and no console/runtime errors appear.
