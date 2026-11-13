export function responseForOperation(operation, result) {
  if (operation === 'claim') return result
  if (operation === 'allocate_listing_id') return { listing_id: result }
  return { ok: true }
}
