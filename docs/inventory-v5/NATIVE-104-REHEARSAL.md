# Isolated 104-row native rehearsal

Status: passed bounded representability and exact reversal checks. Not a production release gate approval.

A separate private test database copied the captured 104 active rows and 52 property definitions. All copied scalar values were checked against the captured rows before conversion. Original rich-text annotations are not claimed to have been copied from production: the exact reversal baseline is the test database's own typed snapshot.

Forward operations preserved all existing property IDs, including the title ID; converted eight rich-text fields to selects; renamed the title; and added Availability, Pipeline Status, Live On, and a numeric formula helper. Every writable candidate value was read back across 104 rows and 55 fields. Numeric formulas matched all 104 serial titles, whose values were unique 1 through 104. Select option names and order matched the staged schema.

A deliberate pause after 52 row patches was read back before the remaining 52 patches were applied. This was a clean interruption checkpoint, not a crash or an uncertain network-flight test. A test rent edit was detected through a changed typed-properties hash before rollback; no inverse write was issued by that check. The injected edit was then explicitly restored and exact readback checked. This does not provide atomic Notion compare-and-swap.

Reversal restored old property types and names first, checked all 52 original definitions, then restored original typed values. Only after exact equality across 104 rows and all original fields were the four test additions removed. Final full schema and typed property JSON matched the test baseline exactly, including IDs, text chunks, whitespace, annotations, and nulls.

The rehearsal caught a real API limit: a rich-text content item over 2,000 characters failed validation. Serialization now splits long content into lossless chunks. No truncation or retry after an uncertain create was used.

## Evidence limits

- The ordered operation log starts with title restoration. Earlier fixture creation is evidenced by individual create responses, not a contemporaneous ordered log.
- Captured content is not a fresh production snapshot. Test property IDs cannot bind a production plan.
- Native readback and disposable SQL restore evidence are separate checks, not a distributed transaction or full deployed end-to-end test.
- Final production view layout/order, runtime equivalence, deployment access, old queue handling, reconciliation, and unknown-flight operational acceptance remain open.
- Area ownership, pet-value provenance, and caption/pin review holds remain. Test candidates are not approved listing readiness.
- The fixture remains private and clearly labeled TEST ONLY, retained for review. Cleanup requires a later review decision.
