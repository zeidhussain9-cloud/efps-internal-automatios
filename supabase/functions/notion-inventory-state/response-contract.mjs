export function responseForOperation(operation, result) {
  if (operation === 'claim') return result
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
