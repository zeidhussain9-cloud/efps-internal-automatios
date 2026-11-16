export function responseForOperation(operation, result) {
  if (['claim', 'record_webhook_event', 'update_webhook_event'].includes(operation)) return result
  if (operation === 'allocate_listing_id') return { listing_id: result }
  return { ok: true }
}

export function missingActivePageRows(activePageIds, snapshotRows) {
  const active = new Set(activePageIds.map((id) => String(id).toLowerCase()))
  return snapshotRows.filter((row) => {
    const pageId = String(row?.source_record?.notion_page_id ?? '').toLowerCase()
    return !pageId || !active.has(pageId)
  })
}


// Canonical Housing fields only. Missing values stay unknown; never fall back to
// the preserved old columns, which are no longer lifecycle inputs.
export function canonicalInventoryState(record) {
  const availability = String(record.Availability ?? '').trim()
  const stage = String(record['Pipeline Status'] ?? '').trim()
  const channels = Array.isArray(record['live at']) ? record['live at'] : []
  return {
    listing_state: ['Available', 'On Hold', 'Rented Out'].includes(availability) ? availability : 'Unknown',
    business_status: ['Needs Review', 'Processing', 'Ready To Post', 'Posted', 'Removed'].includes(stage) ? stage : 'Not recorded',
    channels: channels.filter(x => ['Meta Catalogue', 'WhatsApp Group', 'Housing.com'].includes(x)),
  }
}
