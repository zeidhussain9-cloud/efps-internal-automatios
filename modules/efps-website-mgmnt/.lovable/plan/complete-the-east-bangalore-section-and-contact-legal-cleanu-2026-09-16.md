# Complete the East Bangalore section and contact/legal cleanup

## What will change

1. **East Bangalore cards**
   - Remove “Call about this area” from all six cards.
   - Expand every cluster to 4–5 major nearby localities, using verified spellings and sensible geographic groupings.
   - Replace “Market details: To be confirmed” with a concise factual area profile.
   - Use only current, source-backed transport/geographic facts; no rent, yield, demand, appreciation, inventory, or listing claims.
   - Add a small source link where a card mentions a live transport fact, so visitors can verify it.

2. **Contact section**
   - Remove the repeated outer phone symbol and “Call Us” label.
   - Keep one clear gold “Call Us Now” button with availability hours, without displaying the phone number.
   - Apply the same clean treatment across desktop, tablet, and mobile.

3. **Privacy policy**
   - Add “Privacy Policy” in the footer’s legal area.
   - Open a readable on-page policy dialog covering information collected, purpose, Formspree/Google Forms processing, sharing, retention, security, user choices, and the contact email.
   - Add an acknowledgement beside both enquiry forms, linking to the policy.

4. **Repository and verification**
   - Preserve the landing page’s existing styling and all unrelated sections.
   - Verify formatting, lint, TypeScript, build, browser console, card count/content, phone CTA, policy interaction, and desktop/tablet/mobile layouts.
   - Confirm the final workspace is committed and synced by Lovable to the connected `zeidhussain9-cloud/easyfind-website` repository on `main`.

## Current repository status

The supplied Git settings screenshot confirms `zeidhussain9-cloud/easyfind-website`, branch `main`, is connected and reports “In sync with GitHub.” The sandbox remote is Lovable’s internal mirror, which is expected; Lovable manages the GitHub synchronization.

## Technical details

- Update only `src/routes/index.tsx` for these requested page changes.
- Keep phone digits hidden in visible text while retaining the existing `tel:` destination.
- Keep `info@easyfindprops.com` unchanged.
- Use the existing dialog and button patterns where available; do not add dependencies.
