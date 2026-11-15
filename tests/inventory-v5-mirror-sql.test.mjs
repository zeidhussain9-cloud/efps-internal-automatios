import fs from'node:fs';import assert from'node:assert/strict';import{PGlite}from'@electric-sql/pglite';
const db=new PGlite();await db.exec(`CREATE ROLE anon;CREATE ROLE authenticated;CREATE ROLE service_role;
CREATE TABLE crm_inventory_snapshot(listing_id text PRIMARY KEY,source_kind text,source_tab text,locality text,society_name text,bhk text,monthly_rent numeric,furnishing text,listing_state text,business_status text,intake_status text,pet_friendly text,cloudinary_image_urls jsonb,source_snapshot_at timestamptz,last_synced_at timestamptz,source_record jsonb,source_hash text,deleted_at timestamptz);`);
for(const n of ['20261115145500_inventory_v5_staged.sql','20261115145600_inventory_v5_worker_state.sql','20261115145800_inventory_v5_atomic_mirror.sql'])await db.exec(fs.readFileSync(new URL('../supabase/migrations/'+n,import.meta.url),'utf8'));
const page='12345678-1234-4234-8234-123456789012';
let c=(await db.query("SELECT inventory_v5_worker_state('claim',$1,'EF-2611-ABCD') v",[page])).rows[0].v;
const row={listing_id:'EF-2611-ABCD',source_kind:'housing_notion',inventory_contract_version:5,inventory_revision:0,availability:'Available',pipeline_status:'Ready to Post',live_on:[],source_record:{inventory_contract_version:5,notion_page_id:page},source_hash:'one'};
async function mirror(value,lease=c.lease,revision=value.inventory_revision){return db.query('SELECT inventory_v5_sync_snapshot($1,$2,$3,$4)',[value,page,lease,revision])}
await mirror(row);
// Simulates v4 writer that read before v5 committed: only the DB sees authoritative state.
await assert.rejects(()=>db.exec("UPDATE crm_inventory_snapshot SET inventory_contract_version=4,source_record='{}'"),/downgrade/);
await assert.rejects(()=>mirror({...row,source_hash:'different'}),/reused/);
await db.exec("UPDATE inventory_processing_revisions SET revision=1");
await mirror({...row,inventory_revision:1,source_hash:'two'});
await assert.rejects(()=>mirror(row),/Stale mirror/);
await assert.rejects(()=>db.query('UPDATE crm_inventory_snapshot SET inventory_revision=0 WHERE listing_id=$1',[row.listing_id]),/Stale inventory/);
const q=(await db.query('SELECT inventory_v5_quarantine_identity($1,$2) v',[page,c.lease])).rows[0].v;
assert.equal(q.listing_id,row.listing_id);assert.equal(q.revision,2);
const quarantined=(await db.query('SELECT pipeline_status,business_status,source_record,inventory_revision FROM crm_inventory_snapshot')).rows[0];
assert.equal(quarantined.pipeline_status,'Needs Review');assert.equal(quarantined.business_status,'Needs Review');assert.equal(quarantined.source_record.identity_quarantined,true);assert.equal(quarantined.source_record.notion_page_id,page);
await db.exec("UPDATE inventory_processing_revisions SET lease_until=now()-interval '1 second'");
await assert.rejects(()=>mirror({...row,inventory_revision:1,source_hash:'two'}),/Stale mirror/);
let final=(await db.query('SELECT inventory_revision,source_hash,inventory_contract_version FROM crm_inventory_snapshot')).rows[0];assert.equal(final.inventory_revision,2);assert.equal(final.source_hash,'two');assert.equal(final.inventory_contract_version,5);
console.log('Authoritative DB downgrade/revision fence and transactional lease-fenced mirror checks passed.');await db.close();
