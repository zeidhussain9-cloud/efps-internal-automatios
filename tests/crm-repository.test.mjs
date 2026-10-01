import test from 'node:test';
import assert from 'node:assert/strict';
import {createCrmRepository,normalizeConnectionString,connectionEndpointClass} from '../src/crm-repository.mjs';
test('normalizes direct Supabase URL to IPv4 session pooler',()=>{
 const input='postgresql://postgres:p%40ssword@db.qttcutwzehtskfcwxkwj.supabase.co:5432/postgres';
 const out=normalizeConnectionString(input);
 assert.match(out,/@aws-0-ap-south-1\.pooler\.supabase\.com:5432\/postgres/);
 assert.match(out,/postgres\.qttcutwzehtskfcwxkwj:.*@/);
 assert.ok(!out.includes('sslmode='));
});
test('normalizes a raw special-character password without exposing it',()=>{
 const input='postgresql://postgres:p@ss#word@db.qttcutwzehtskfcwxkwj.supabase.co:5432/postgres';
 const out=normalizeConnectionString(input);
 assert.equal(out.includes('@aws-0-ap-south-1.pooler.supabase.com:5432/postgres'),true);
 assert.equal(out.includes('postgres.qttcutwzehtskfcwxkwj:'),true);
 assert.match(out,/p%40ss%23word/);
});
test('reports normalized endpoint class without exposing connection details',()=>{
 assert.equal(connectionEndpointClass('postgresql://postgres:fictional@db.qttcutwzehtskfcwxkwj.supabase.co:5432/postgres'),'supabase_session_pooler_ipv4');
 assert.equal(connectionEndpointClass('postgresql://postgres:fictional@db.example.invalid:5432/postgres'),'external_or_unknown');
 assert.equal(connectionEndpointClass('not-a-url'),'invalid_url');
 assert.equal(connectionEndpointClass('postgresql://postgres:p@ss#word@db.qttcutwzehtskfcwxkwj.supabase.co:5432/postgres'),'supabase_session_pooler_ipv4');
});
test('leaves non-Supabase URLs unchanged',()=>{
 const input='postgresql://postgres:fictional@db.example.invalid:5432/postgres';
 assert.equal(normalizeConnectionString(input),input);
});
test('repository validates limits and uses parameterized SQL',async()=>{
 const calls=[];const pool={query:async(sql,args)=>{calls.push({sql,args});return {rows:sql.startsWith('SELECT 1')?[{ok:1}]:[{id:'L-1'}]};}};
 const repo=createCrmRepository({pool});
 assert.equal(await repo.health(),true);
 assert.deepEqual(await repo.listLeads(10),[{id:'L-1'}]);
 assert.deepEqual(await repo.getLead('L-1'),{id:'L-1'});
 assert.deepEqual(calls[1].args,[10]);assert.deepEqual(calls[2].args,['L-1']);
 await assert.rejects(()=>repo.listLeads(101),/Invalid limit/);
 await assert.rejects(()=>repo.getLead(''),/Invalid lead ID/);
});


test('lead inbox returns conversation timeline fields and validates server-side sorting',async()=>{
 const calls=[];
 const pool={query:async(sql,args)=>{
  calls.push({sql,args});
  if(sql.startsWith('SELECT count(*)::int AS total'))return{rows:[{total:186}]};
  return{rows:[{id:'L-LIVE-1',contacted_at:'2026-08-26T07:30:00.000Z',last_message_direction:'Incoming',last_message_at:'2026-09-30T16:26:15.000Z'}]};
 }};
 const cr= createCrmRepository({pool});
 const data=await cr.listLeadsPage(100,0,'+919148338801','', 'customer_waiting','shiv');
 assert.equal(data.sort,'customer_waiting');
 assert.equal(data.total,186);
 assert.equal(data.leads[0].last_message_direction,'Incoming');
 assert.match(calls[0].sql,/contacted_at/);
 assert.match(calls[0].sql,/last_message_at/);
 assert.match(calls[0].sql,/ORDER BY \(last_message\.last_message_direction='Incoming'\) DESC/);
 assert.deepEqual(calls[0].args,['+919148338801','%shiv%',100,0]);
 assert.match(calls[0].sql,/lower\(coalesce\(l\.display_name,l\.normalized_phone,''\)\) LIKE/);
 await assert.rejects(()=>cr.listLeadsPage(100,0,'+919148338801','', 'unsupported_sort'),/Invalid lead sort/);
});

test('durable lead mutation is transactional and writes an audit event',async()=>{
 const calls=[];
 const client={query:async(sql,args)=>{calls.push(['client',sql,args]);if(sql.startsWith('INSERT INTO crm_leads'))return{rows:[{id:'L-1001',display_name:'A'}]};if(sql.startsWith('INSERT INTO crm_activity'))return{rows:[{id:1}]};return{rows:[]}},release:()=>calls.push(['release'])};
 const pool={connect:async()=>client};
 const repo=createCrmRepository({pool});
 const row=await repo.createLead({id:'L-1001',displayName:'A',actor:'pilot',requirements:{bhk:2}});
 assert.equal(row.id,'L-1001');assert.equal(calls[0][1],'BEGIN');assert.match(calls[1][1],/^INSERT INTO crm_leads/);assert.match(calls[2][1],/^INSERT INTO crm_activity/);assert.equal(calls[3][1],'COMMIT');assert.equal(calls[4][0],'release');
});
test('provider event deduplication relies on a database unique key',async()=>{
 const calls=[];const pool={query:async(sql,args)=>{calls.push([sql,args]);return{rows:[]}}};
 const repo=createCrmRepository({pool});
 const result=await repo.recordProviderEvent({provider:'test',providerEventId:'evt-1',eventType:'message',payload:{id:1}});
 assert.deepEqual(result,{inserted:false,id:null});assert.match(calls[0][0],/ON CONFLICT\(provider,provider_event_id\) DO NOTHING/);
});
test('AI cursor is upserted per lead',async()=>{
 const calls=[];const pool={query:async(sql,args)=>{calls.push([sql,args]);return{rows:[{lead_id:'L-1001',source_number:'wa-1',last_message_id:7,last_message_at:'2026-10-01T00:00:00Z'}]}}};
 const repo=createCrmRepository({pool});
 const row=await repo.setAiCursor({leadId:'L-1001',sourceNumber:'wa-1',lastMessageId:7,lastMessageAt:'2026-10-01T00:00:00Z'});assert.equal(row.lead_id,'L-1001');assert.match(calls[0][0],/ON CONFLICT\(lead_id\) DO UPDATE/);
});

test('lead status validation accepts Out of Coverage Area and rejects unknown statuses',async()=>{
 const calls=[];
 const client={query:async(sql,args)=>{calls.push([sql,args]);if(sql.startsWith('UPDATE crm_leads'))return{rows:[{id:'L-OOC',lead_type:'Out of Coverage Area'}]};return{rows:[]}},release:()=>{}};
 const repo=createCrmRepository({pool:{connect:async()=>client}});
 const row=await repo.updateLead({id:'L-OOC',leadType:'Out of Coverage Area',actor:'pilot'});
 assert.equal(row.lead_type,'Out of Coverage Area');
 assert.match(calls[2][0],/INSERT INTO crm_activity/);
 await assert.rejects(()=>repo.updateLead({id:'L-OOC',leadType:'Outside Bengaluru',actor:'pilot'}),/Invalid lead status/);
});

test('property media accepts only Cloudinary external references',async()=>{
 const calls=[];const pool={query:async(sql,args)=>{calls.push([sql,args]);return{rows:[{listing_id:'EF-1',media_url:args[1]}]}}};
 const repo=createCrmRepository({pool});
 const row=await repo.addPropertyMedia({listingId:'EF-1',mediaUrl:'https://res.cloudinary.com/demo/image/upload/v1/ef-1.jpg',cloudinaryPublicId:'ef-1'});
 assert.equal(row.listing_id,'EF-1');assert.match(calls[0][0],/crm_property_media/);
 await assert.rejects(()=>repo.addPropertyMedia({listingId:'EF-1',mediaUrl:'https://example.com/ef-1.jpg'}),/Cloudinary media URL/);
});

test('provider event claiming is lock-protected and refuses already processed events',async()=>{
 const calls=[];
 const client={query:async(sql,args)=>{calls.push([sql,args]);if(sql.startsWith('SELECT id,status,attempts'))return{rows:[{id:7,status:'received',attempts:1}]};return{rows:[]}},release:()=>{}};
 const repo=createCrmRepository({pool:{connect:async()=>client}});
 const claim=await repo.claimProviderEvent({provider:'whapi',providerEventId:'evt-7'});
 assert.deepEqual(claim,{claimed:true,id:7,status:'processing',attempts:2});
 assert.match(calls[2][0],/UPDATE crm_provider_events SET status/);
});
test('provider event completion records processed timestamp or failure',async()=>{
 const calls=[];const pool={query:async(sql,args)=>{calls.push([sql,args]);return{rows:[{id:7,status:args[0]}]}}};const repo=createCrmRepository({pool});
 const row=await repo.completeProviderEvent({id:7,status:'processed'});assert.equal(row.status,'processed');assert.match(calls[0][0],/processed_at/);
 await assert.rejects(()=>repo.completeProviderEvent({id:0}),/Invalid provider event completion/);
});

test('property matching expands historical BHK and locality requirements without guessing', async()=>{
 const calls=[];
 const {createCrmRepository}=await import('../src/crm-repository.mjs');
 const repo=createCrmRepository({pool:{query:async(sql,params)=>{calls.push({sql,params});return{rows:[]}}}});
 await repo.matchInventory({bhk:'1BHK/2BHK',budget:40000,locality:'Kasavanahalli, Harlur, HSR Layout',furnishing:'Semi Furnished',petFriendly:'Yes',limit:10});
 assert.equal(calls.length,1);
 const {sql,params}=calls[0];
 assert.match(sql,/bhk = ANY/);
 assert.deepEqual(params[2],['1 BHK','2 BHK']);
 assert.match(sql,/locality ILIKE/);
 assert.deepEqual(params.at(-1),10);
});

test('lead workspace reads the AI cursor for the selected lead',async()=>{
 const calls=[];
 const pool={query:async(sql,args)=>{calls.push({sql,args});return{rows:[]}}};
 const repo=createCrmRepository({pool});
 await repo.getLeadWorkspace('L-LIVE-1','+919148338801');
 const cursorCall=calls.find(x=>x.sql.includes('crm_ai_cursors'));
 assert.ok(cursorCall);
 assert.match(cursorCall.sql,/WHERE lead_id=\$1 AND source_number=\$2/);
 assert.deepEqual(cursorCall.args,['L-LIVE-1','+919148338801']);
});

test('follow-up create and complete write durable activity entries',async()=>{
 const calls=[];
 const client={query:async(sql,args)=>{
  calls.push([sql,args]);
  if(sql==='BEGIN'||sql==='COMMIT'||sql==='ROLLBACK')return{rows:[]};
  if(sql.startsWith('INSERT INTO crm_followups'))return{rows:[{id:'FU-1',lead_id:'L-1'}]};
  if(sql.startsWith('UPDATE crm_followups'))return{rows:[{id:'FU-1',lead_id:'L-1',completed_at:'2026-10-01T00:00:00Z'}]};
  if(sql.startsWith('INSERT INTO crm_activity'))return{rows:[{id:1}]};
  return{rows:[]};
 },release:()=>{}};
 const pool={connect:async()=>client};
 const repo=createCrmRepository({pool});
 const created=await repo.addFollowup({id:'FU-1',leadId:'L-1',dueAt:'2026-10-02T10:00:00',note:'Call customer',actor:'pilot'});
 assert.equal(created.id,'FU-1');
 const completed=await repo.completeFollowup({id:'FU-1',actor:'pilot'});
 assert.equal(completed.id,'FU-1');
 assert.equal(calls.filter(x=>x[0].startsWith('INSERT INTO crm_activity')).length,2);
});
