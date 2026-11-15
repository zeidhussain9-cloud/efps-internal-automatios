import fs from 'node:fs';import assert from 'node:assert/strict';import{PGlite}from'@electric-sql/pglite';
const db=new PGlite();await db.exec('CREATE ROLE anon;CREATE ROLE authenticated;CREATE ROLE service_role;CREATE TABLE public.crm_inventory_snapshot(listing_id text PRIMARY KEY);');
for(const f of ['20261115145500_inventory_v5_staged.sql','20261115145700_inventory_v5_reference_order.sql'])await db.exec(fs.readFileSync(new URL('../supabase/migrations/'+f,import.meta.url),'utf8'));
const ids=Array.from({length:4},(_,i)=>`12345678-1234-4234-8234-${String(i+1).padStart(12,'0')}`);
async function ref(op,args={}){return(await db.query(`SELECT public.inventory_v5_reference_order(p_operation=>$1,p_page_id=>$2,p_listing_id=>$3,p_seed=>$4) AS v`,[op,args.page??null,args.listing??null,args.seed??null])).rows[0].v}
async function job(op,args={}){return(await db.query(`SELECT public.inventory_v5_renumber_state(p_operation=>$1,p_job_id=>$2,p_lease=>$3,p_next_offset=>$4) AS v`,[op,args.id??null,args.lease??null,args.offset??null])).rows[0].v}
let x=await ref('seed',{seed:ids.slice(0,3).map((page_id,i)=>({page_id,listing_id:'EF-'+i}))});assert.deepEqual(x.page_ids,ids.slice(0,3));
await assert.rejects(()=>ref('seed',{seed:[]}),/already seeded/);
const first=await job('claim');assert.equal(first.status,'running');assert.deepEqual(first.ordered_page_ids,ids.slice(0,3));assert.equal((await job('claim')).busy,true);
x=await ref('activate',{page:ids[3],listing:'EF-3'});assert.deepEqual(x.page_ids,[ids[3],...ids.slice(0,3)]);
assert.equal((await job('claim')).busy,true); // new row waits for current pass
const valid={id:first.job_id,lease:first.lease_token};
await assert.rejects(()=>job('finish',valid),/incomplete/);
await job('checkpoint',{...valid,offset:2});await assert.rejects(()=>job('checkpoint',{...valid,offset:1}),/checkpoint/);
await job('checkpoint',{...valid,offset:3});await job('finish',valid);
const next=await job('claim');assert.deepEqual(next.ordered_page_ids,[ids[3],...ids.slice(0,3)]);
await assert.rejects(()=>job('checkpoint',{...valid,offset:3}),/Stale renumber/);
await ref('deactivate',{page:ids[1],listing:'EF-1'});x=await ref('read');assert.deepEqual(x.page_ids,[ids[3],ids[0],ids[2]]);
const n=await db.query("SELECT count(*)::int AS n FROM inventory_renumber_jobs WHERE status='pending'");assert.equal(n.rows[0].n,1);
console.log('Isolated reference ordering, concurrent insertion coalescing, resume/checkpoint fencing checks passed.');await db.close();
