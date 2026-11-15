import fs from 'node:fs';
import assert from 'node:assert/strict';
import { PGlite } from '@electric-sql/pglite';
const db = new PGlite();
await db.exec('CREATE ROLE anon; CREATE ROLE authenticated; CREATE ROLE service_role; CREATE TABLE public.crm_inventory_snapshot(listing_id text PRIMARY KEY);');
const migration=fs.readFileSync(new URL('../supabase/migrations/20261115145500_inventory_v5_staged.sql', import.meta.url),'utf8');
await db.exec(migration);
await db.exec(`INSERT INTO crm_inventory_snapshot(listing_id) VALUES ('legacy');`);
let x=await db.query('SELECT inventory_contract_version,live_on FROM crm_inventory_snapshot');
assert.equal(x.rows[0].inventory_contract_version,4);assert.equal(x.rows[0].live_on,null);
await db.exec(`INSERT INTO crm_inventory_snapshot(listing_id,availability,pipeline_status,live_on,inventory_contract_version) VALUES ('new','On Hold','Ready to Post',ARRAY[]::text[],5);`);
for (const bad of ["ARRAY['Unknown']","ARRAY['Meta Catalogue','Meta Catalogue']","ARRAY[NULL]::text[]"]) {
 let rejected=false;try {await db.exec(`UPDATE crm_inventory_snapshot SET live_on=${bad} WHERE listing_id='new';`);}catch(e){rejected=true;}assert.equal(rejected,true,bad);
}
for (const sql of ["UPDATE crm_inventory_snapshot SET availability='Maybe' WHERE listing_id='new'", "UPDATE crm_inventory_snapshot SET live_on=NULL WHERE listing_id='new'", "INSERT INTO inventory_field_provenance(listing_id,field_name,origin) VALUES('new','BHK','guessed')"]) {
 let rejected=false;try{await db.exec(sql);}catch(e){rejected=true;}assert.equal(rejected,true,sql);
}
await db.exec(`INSERT INTO inventory_field_provenance(listing_id,field_name,origin,last_generated_value) VALUES('new','flat_furnishings','derived','"Semi Package"');`);
await db.exec(`INSERT INTO inventory_renumber_jobs(membership_hash,ordered_page_ids,status) VALUES ('a',ARRAY[]::uuid[],'running');`);
let locked=false;try{await db.exec(`INSERT INTO inventory_renumber_jobs(membership_hash,ordered_page_ids,status) VALUES ('b',ARRAY[]::uuid[],'running');`);}catch(e){locked=true;}assert.equal(locked,true);
const roles=await db.query(`SELECT relname,relrowsecurity FROM pg_class WHERE relname IN ('inventory_field_provenance','inventory_processing_revisions','inventory_reference_order','inventory_renumber_jobs')`);
assert.equal(roles.rows.length,4);assert.ok(roles.rows.every(r=>r.relrowsecurity));
console.log(JSON.stringify({migration:'applied in isolated PGlite PostgreSQL only',tests:['legacy compatibility null vs empty','v5 completeness','channel membership','channel uniqueness','no null channels','availability vocabulary','provenance origin','one renumber writer','RLS enabled'],passed:true,live_mutations:0},null,2));
await db.close();
