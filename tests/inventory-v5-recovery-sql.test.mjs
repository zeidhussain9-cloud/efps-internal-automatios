import fs from'node:fs';import assert from'node:assert/strict';import{PGlite}from'@electric-sql/pglite';
const db=new PGlite();await db.exec('CREATE ROLE anon;CREATE ROLE authenticated;CREATE ROLE service_role;CREATE TABLE crm_inventory_snapshot(listing_id text PRIMARY KEY);');
for(const n of ['20261115145500_inventory_v5_staged.sql','20261115145600_inventory_v5_worker_state.sql','20261115145700_inventory_v5_reference_order.sql','20261115145900_inventory_v5_recovery.sql'])await db.exec(fs.readFileSync(new URL('../supabase/migrations/'+n,import.meta.url),'utf8'));
const page='12345678-1234-4234-8234-123456789012';
let claim=(await db.query("SELECT inventory_v5_worker_state('claim',$1,'EF-2611-ABCD')v",[page])).rows[0].v;
await db.query("SELECT inventory_v5_worker_state(p_operation=>'begin_effect',p_page_id=>$1,p_lease=>$2,p_values=>$3)",[page,claim.lease,{patch:{x:2}}]);
const effect=(await db.query('SELECT active_effect FROM inventory_processing_revisions')).rows[0].active_effect;
await db.exec("UPDATE inventory_processing_revisions SET lease_until=now()-interval '1 second'");
async function recover(id,expected=effect){return db.query('SELECT inventory_v5_recover_effect($1,$2,$3,$4)',[id,expected,{x:2},{}])}
await assert.rejects(()=>recover(page),/attestation/);
// Database owner records exact independent proof. This is synthetic evidence,
// never a claim that local death or a timeout proves a real Notion request ended.
let id=(await db.query("INSERT INTO inventory_effect_recovery_attestations(scope,page_id,effect,writer_reference,remote_reference,request_reference) VALUES('worker',$1,$2,'synthetic stopped writer','synthetic terminal remote response','request123') RETURNING id",[page,effect])).rows[0].id;
await db.exec('SET ROLE service_role');
await assert.rejects(()=>db.query("INSERT INTO inventory_effect_recovery_attestations(scope,page_id,effect,writer_reference,remote_reference,request_reference) VALUES('worker',$1,$2,'a','b','c')",[page,effect]),/permission denied/);
await assert.rejects(()=>recover(id,{...effect,lease:'different'}),/attestation/);
await recover(id);await assert.rejects(()=>recover(id),/attestation/);
await db.exec('RESET ROLE');
let final=(await db.query('SELECT active_effect FROM inventory_processing_revisions')).rows[0];assert.equal(final.active_effect,null);
const next=(await db.query("SELECT inventory_v5_worker_state('claim',$1,'EF-2611-ABCD')v",[page])).rows[0].v;assert.ok(next.lease);
console.log('Operator-attested exact-effect recovery, no worker self-attestation, single-use CAS checks pass.');await db.close();
