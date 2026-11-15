// Shared by the staged Edge adapter and Node contract tests. No side effects.
export const inventoryV5Channels = ['Meta Catalogue', 'WhatsApp Group', 'Housing.com']
export function v5Projection(record) {
  if (Number(record.inventory_contract_version ?? 4) !== 5) return {}
  const availability = record.Availability
  const pipeline = record['Pipeline Status']
  const channels = record['Live On']
  if (!['Available', 'On Hold', 'Rented Out'].includes(availability)) throw new Error('Invalid Availability')
  if (!['Needs Review', 'Processing', 'Ready to Post', 'Removed'].includes(pipeline)) throw new Error('Invalid Pipeline Status')
  if (!Array.isArray(channels) || channels.some(x => !inventoryV5Channels.includes(x)) || new Set(channels).size !== channels.length) throw new Error('Invalid Live On array')
  const onboarded = record.onboarded_at
  if (onboarded !== null && onboarded !== undefined && (typeof onboarded !== 'string' || !/^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/.test(onboarded) || !Number.isFinite(Date.parse(onboarded)))) throw new Error('Invalid qualified onboarding timestamp')
  return { availability, pipeline_status: pipeline, live_on: [...channels], onboarded_at: onboarded ?? null, inventory_contract_version: 5 }
}

export function effectiveInventoryState(row) {
  if (Number(row.inventory_contract_version ?? 4) === 5) return { availability: row.availability, pipeline: row.pipeline_status, liveOn: row.live_on ?? [] }
  return { availability: row.listing_state, pipeline: null, liveOn: null }
}

export function mayDistribute(row) {
  const state = effectiveInventoryState(row)
  return Number(row.inventory_contract_version ?? 4) === 5 && state.availability === 'Available' && state.pipeline === 'Ready to Post'
}
