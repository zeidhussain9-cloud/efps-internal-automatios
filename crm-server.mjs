import {createServer} from 'node:http';
import {randomUUID,createHmac,timingSafeEqual} from 'node:crypto';
import {readFile,stat} from 'node:fs/promises';
import {join,extname,resolve} from 'node:path';
import {authorized,accessMode} from './src/server-auth.mjs';
import {getRequestPrincipal,loginWithPassword,revokeRequestSession,sessionCookie,clearSessionCookie,sameOrigin,sessionPolicy} from './src/server-session.mjs';
import {analyzeRealLead} from './src/ollama-adapter.mjs';
import {createCrmRepository} from './src/crm-repository.mjs';
import {normalizeInventorySort,sortInventoryRows} from './src/inventory-logic.mjs';
import {createCrmClassificationRepository} from './src/crm-classification-repository.mjs';
import {draftPreflight} from './src/draft-preflight.mjs';
import {startupDatabaseCheck} from './src/crm-startup-check.mjs';
const root=resolve('dist');
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.ico':'image/x-icon'};
async function readJsonBody(req,maxBytes=16384){let raw='';for await(const chunk of req){raw+=chunk;if(Buffer.byteLength(raw,'utf8')>maxBytes)throw Object.assign(Error('Request too large'),{statusCode:413})}if(!raw.trim())return{};try{const value=JSON.parse(raw);if(!value||typeof value!=='object'||Array.isArray(value))throw Error('JSON object required');return value}catch{throw Object.assign(Error('Invalid JSON body'),{statusCode:400})}}
const security={'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Frame-Options':'DENY','Cache-Control':'no-store','Strict-Transport-Security':'max-age=31536000','Permissions-Policy':'geolocation=(),camera=(),microphone=()','Cross-Origin-Opener-Policy':'same-origin','Cross-Origin-Resource-Policy':'same-origin','X-Permitted-Cross-Domain-Policies':'none','Content-Security-Policy':"default-src 'self'; img-src 'self' https: data:; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' https://qttcutwzehtskfcwxkwj.supabase.co wss://qttcutwzehtskfcwxkwj.supabase.co; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"};
createServer(async(req,res)=>{
 try{
  const p=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
  if(p==='/health'){res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({ok:true}));}
  if(p==='/api/internal/inventory/sync'&&req.method==='POST'){
   if(process.env.CRM_INVENTORY_SYNC_ENABLED!=='true'||!process.env.CRM_INVENTORY_SYNC_SECRET){res.writeHead(404,security);return res.end('Inventory sync disabled');}
   const ts=String(req.headers['x-efps-inventory-timestamp']||'');const provided=String(req.headers['x-efps-inventory-signature']||'');
   if(!/^\d+$/.test(ts)||Math.abs(Date.now()-Number(ts)*1000)>300000||!/^[a-f0-9]{64}$/i.test(provided)){res.writeHead(401,security);return res.end('Invalid inventory sync authentication');}
   const expected=createHmac('sha256',process.env.CRM_INVENTORY_SYNC_SECRET).update(ts).digest('hex');
   if(expected.length!==provided.length||!timingSafeEqual(Buffer.from(expected),Buffer.from(provided.toLowerCase()))){res.writeHead(401,security);return res.end('Invalid inventory sync authentication');}
   try{const {readCanonicalInventory,syncInventorySnapshot}=await import('./src/inventory-sync.mjs');const rows=await readCanonicalInventory(process.env);const result=await syncInventorySnapshot({rows});res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({ok:true,...result}));}
   catch(e){res.writeHead(502,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({ok:false,error:'Inventory sync failed'}));}
  }
  const mode=accessMode(process.env);
  if(mode==='misconfigured'){res.writeHead(503,security);return res.end('CRM access configuration incomplete');}
  if(p==='/api/auth/session'&&req.method==='GET'){
   const principal=getRequestPrincipal(req,process.env);res.writeHead(200,{...security,'Content-Type':'application/json'});
   return res.end(JSON.stringify({authenticated:Boolean(principal),user:principal?.user||null,policy:sessionPolicy()}));
  }
  if(p==='/api/auth/login'&&req.method==='POST'){
   if(mode!=='protected'){res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({authenticated:true,user:'local-operator',policy:sessionPolicy()}))}
   if(!sameOrigin(req)){res.writeHead(403,security);return res.end('Cross-origin sign-in rejected')}
   let body={};try{body=await readJsonBody(req,8192)}catch(e){res.writeHead(e.statusCode||400,security);return res.end(e.message)}
   const result=loginWithPassword(req,{username:body.username,password:body.password,env:process.env});
   if(!result.ok){res.writeHead(result.status,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:result.error}))}
   if(process.env.DATABASE_URL){const auditRepo=createCrmRepository();try{await auditRepo.appendActivity({leadId:null,actor:result.user,action:'auth.login',details:{via:'password'}})}catch{}finally{await auditRepo.close()}}
   res.writeHead(200,{...security,'Content-Type':'application/json','Set-Cookie':sessionCookie(result.token,req)});
   return res.end(JSON.stringify({authenticated:true,user:result.user,policy:sessionPolicy()}));
  }
  if(p==='/api/auth/logout'&&req.method==='POST'){
   if(!sameOrigin(req)){res.writeHead(403,security);return res.end('Cross-origin logout rejected')}
   const principal=getRequestPrincipal(req,process.env);revokeRequestSession(req);
   if(principal&&process.env.DATABASE_URL){const auditRepo=createCrmRepository();try{await auditRepo.appendActivity({leadId:null,actor:principal.user,action:'auth.logout',details:{via:principal.via}})}catch{}finally{await auditRepo.close()}}
   res.writeHead(204,{...security,'Set-Cookie':clearSessionCookie(req)});return res.end();
  }
  const principal=mode==='protected'?getRequestPrincipal(req,process.env):{user:'local-operator',via:'development'};
  if(mode==='protected'&&!principal&&p.startsWith('/api/')){
   res.writeHead(401,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:'Authentication required'}));
  }
  if(!sameOrigin(req)&&!['GET','HEAD'].includes(req.method)&&p!=='/api/internal/inventory/sync'){res.writeHead(403,security);return res.end('Cross-origin request rejected')}
  if(p==='/api/audit/recent'){
   if(req.method!=='GET'){res.writeHead(405,security);return res.end('Method not allowed')}
   const q=new URL(req.url,'http://localhost').searchParams;const limitRaw=q.get('limit')||'50';
   if(!/^\d{1,3}$/.test(limitRaw)){res.writeHead(400,security);return res.end('Invalid limit')}
   const repo=createCrmRepository();try{const rows=await repo.listGlobalActivity(Number(limitRaw));res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({rows}))}finally{await repo.close()}
  }
  if(p==='/api/db/export'&&req.method==='GET'){
   if(process.env.CRM_DB_READ_ENABLED!=='true'||!process.env.DATABASE_URL){res.writeHead(404,security);return res.end('Export unavailable')}
   const source=new URL(req.url,'http://localhost').searchParams.get('source_number')||'+919148338801';const repo=createCrmRepository();
   try{
    const rows=await repo.exportLeads(source);
    if(principal){try{await repo.appendActivity({leadId:null,actor:principal.user,action:'data.export',details:{source_number:source,row_count:rows.length,format:'csv'}})}catch{}}
    const esc=v=>'"'+String(v??'').replace(/"/g,'""')+'"';const head=['id','display_name','phone','lead_status','tenant_type','priority','classification','source_number','updated_at'];
    const csv=[head.join(','),...rows.map(r=>[r.id,r.display_name,r.normalized_phone,r.lead_type,r.tenant_type,r.priority,r.classification,r.source_number,r.updated_at].map(esc).join(','))].join('\n')+'\n';
    res.writeHead(200,{...security,'Content-Type':'text/csv; charset=utf-8','Content-Disposition':'attachment; filename="easyfind-crm-export.csv"'});return res.end(csv);
   }finally{await repo.close()}
  }
  if(process.env.CRM_DB_WRITE_ENABLED==='true'&&mode==='protected'&&principal&&req.method==='POST'&&/^\/api\/db\/leads\/[^/]+\/(archive|restore)$/.test(p)){
   const id=decodeURIComponent(p.split('/')[4]);const action=p.split('/')[5];if(!id||id.length>128){res.writeHead(400,security);return res.end('Invalid lead ID')}
   const repo=createCrmRepository();try{const row=action==='archive'?await repo.archiveLead({id,actor:principal.user}):await repo.restoreLead({id,actor:principal.user});if(!row){res.writeHead(404,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:'Lead not found'}))}res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify(row))}catch(e){res.writeHead(e.statusCode||422,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:'Lead '+action+' failed'}))}finally{await repo.close()}
  }
  // Durable database writes: explicit opt-in, protected access and audited in the same transaction.
  if((process.env.CRM_CLASSIFICATION_WRITE_ENABLED==='true'||process.env.CRM_DB_WRITE_ENABLED==='true')&&mode==='protected'&&req.method==='POST'&&p.startsWith('/api/db/classifications/')){
   if(!process.env.DATABASE_URL){res.writeHead(404,security);return res.end('Database write pilot disabled');}
   const id=decodeURIComponent(p.slice('/api/db/classifications/'.length));if(!/^\d+$/.test(id)){res.writeHead(400,security);return res.end('Invalid classification ID');}
   const body=await readJsonBody(req);const repo=createCrmClassificationRepository();
   try{const result=await repo.classify({id:Number(id),code:String(body.classification||''),source:String(body.source||'operator'),confidence:body.confidence===null||body.confidence===undefined?null:Number(body.confidence),actor:principal?.user||process.env.CRM_BASIC_AUTH_USERNAME||'operator'});res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify(result));}
   catch(e){const status=e?.statusCode||422;res.writeHead(status,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:e.message==='Invalid classification'?'Invalid classification':status===404?'Classification not found':'Classification update failed'}));}
   finally{await repo.close();}
  }
  if(process.env.CRM_DB_WRITE_ENABLED==='true'&&mode==='protected'&&req.method!=='GET'&&(p==='/api/db/leads'||p.startsWith('/api/db/leads/')||p==='/api/db/followups'||p.startsWith('/api/db/followups/'))&&!p.match(/^\/api\/db\/leads\/[^/]+\/requirements$/)){
   if(!process.env.DATABASE_URL){res.writeHead(404,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:'Database write pilot disabled'}));}
   const repo=createCrmRepository();const actor=principal?.user||process.env.CRM_BASIC_AUTH_USERNAME;
   try{
    if(p==='/api/db/leads'&&req.method==='POST'){
     const body=await readJsonBody(req);const lead=await repo.createLead({id:body.id,displayName:body.displayName,normalizedPhone:body.normalizedPhone,status:body.status,priority:body.priority,requirements:body.requirements,operatorNotes:body.operatorNotes,actor});res.writeHead(201,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify(lead));
    }
    if(p.startsWith('/api/db/leads/')&&req.method==='PATCH'){
     const id=decodeURIComponent(p.slice('/api/db/leads/'.length));if(!id||id.includes('/')||id.length>128){res.writeHead(400,security);return res.end('Invalid lead ID')}
     const body=await readJsonBody(req);const lead=await repo.updateLead({id,displayName:body.displayName,normalizedPhone:body.normalizedPhone,status:body.status,leadType:body.leadType,tenantType:body.tenantType,priority:body.priority,requirements:body.requirements,operatorNotes:body.operatorNotes,actor});if(!lead){res.writeHead(404,security);return res.end('Lead not found')}res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify(lead));
    }
    if(p.match(/^\/api\/db\/leads\/[^/]+\/activity$/)&&req.method==='POST'){
     const id=decodeURIComponent(p.split('/')[4]);const body=await readJsonBody(req);const row=await repo.appendActivity({leadId:id,actor,action:body.action,details:body.details});res.writeHead(201,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify(row));
    }
    if(p.match(/^\/api\/db\/leads\/[^/]+\/evidence$/)&&req.method==='POST'){
     const id=decodeURIComponent(p.split('/')[4]);const body=await readJsonBody(req);const row=await repo.appendRequirementEvidence({leadId:id,fieldName:body.fieldName,value:body.value,sourceMessageId:body.sourceMessageId,sourceNumber:body.sourceNumber,actor});res.writeHead(201,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify(row));
    }
    if(p==='/api/db/followups'&&req.method==='POST'){
     const body=await readJsonBody(req);const row=await repo.addFollowup({id:body.id||randomUUID(),leadId:body.leadId,dueAt:body.dueAt,note:body.note,actor});res.writeHead(201,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify(row));
    }
    if(p.match(/^\/api\/db\/followups\/[^/]+\/complete$/)&&req.method==='POST'){
     const id=decodeURIComponent(p.split('/')[4]);const row=await repo.completeFollowup({id,actor});if(!row){res.writeHead(404,security);return res.end('Follow-up not found')}res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify(row));
    }
    if(p==='/api/db/leads' || p.startsWith('/api/db/leads/') || p.startsWith('/api/db/followups/')){res.writeHead(405,security);return res.end('Method not allowed')}
   }catch(e){const status=e?.statusCode||((e?.code==='23505')?409:422);res.writeHead(status,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:status===409?'Conflict':e?.message==='Request too large'?'Request too large':'Database write rejected'}));}
   finally{await repo.close()}
  }
  if(p==='/api/db/classifications'){
   if(process.env.CRM_DB_READ_ENABLED!=='true'||!process.env.DATABASE_URL||mode!=='protected'){res.writeHead(404,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:'Classification database disabled'}));}
   if(req.method!=='GET'){res.writeHead(405,security);return res.end('Method not allowed');}
   const q=new URL(req.url,'http://localhost').searchParams;
   const limitRaw=q.get('limit')||'100',offsetRaw=q.get('offset')||'0';
   if(!/^\d{1,3}$/.test(limitRaw)||!/^\d{1,7}$/.test(offsetRaw)){res.writeHead(400,security);return res.end('Invalid pagination');}
   const repo=createCrmClassificationRepository();
   try{const data=await repo.list({limit:Number(limitRaw),offset:Number(offsetRaw),status:q.get('status')||'',classification:q.get('classification')||'',sourceNumber:q.get('source_number')||'+919148338801'});res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify(data));}
   finally{await repo.close();}
  }

  if(process.env.CRM_DB_WRITE_ENABLED==='true'&&mode==='protected'&&principal&&p.match(/^\/api\/db\/leads\/[^/]+\/requirements$/)&&req.method==='PATCH'){
   const id=decodeURIComponent(p.split('/')[4]);const body=await readJsonBody(req,32768);const repo=createCrmRepository();
   try{const profile=await repo.upsertLeadRequirements({leadId:id,profile:body.profile||{},actor:principal.user});res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify(profile))}
   catch(e){res.writeHead(e?.code==='23514'?422:500,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:e.message||'Requirement update failed'}))}
   finally{await repo.close()}
  }
  if(process.env.CRM_DB_WRITE_ENABLED==='true'&&mode==='protected'&&principal&&p.match(/^\/api\/ai\/runs\/[^/]+\/accept$/)&&req.method==='POST'){
   const id=decodeURIComponent(p.split('/')[4]);const repo=createCrmRepository();try{const result=await repo.applyAiRun({id,actor:principal.user});res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify(result))}catch(e){res.writeHead(422,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:e.message||'AI requirement acceptance failed'}))}finally{await repo.close()}
  }
  if(process.env.CRM_DB_WRITE_ENABLED==='true'&&mode==='protected'&&principal&&p.match(/^\/api\/ai\/runs\/[^/]+\/reject$/)&&req.method==='POST'){
   const id=decodeURIComponent(p.split('/')[4]);const repo=createCrmRepository();try{const row=await repo.decideAiRun({id,status:'rejected',actor:principal.user});res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify(row))}catch(e){res.writeHead(422,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:e.message||'AI rejection failed'}))}finally{await repo.close()}
  }
  if(process.env.CRM_DB_WRITE_ENABLED==='true'&&mode==='protected'&&principal&&p.match(/^\/api\/db\/leads\/[^/]+\/drafts$/)&&req.method==='POST'){
   const id=decodeURIComponent(p.split('/')[4]);const body=await readJsonBody(req,8192);const repo=createCrmRepository();try{const row=await repo.saveDraft({leadId:id,body:String(body.body||''),actor:principal.user,aiRunId:body.aiRunId||null,aiProvider:String(body.aiProvider||'unknown'),modelName:String(body.modelName||'unknown'),evidenceMessageIds:Array.isArray(body.evidenceMessageIds)?body.evidenceMessageIds.map(Number).filter(Number.isInteger):[],evidenceSummary:String(body.evidenceSummary||'')});res.writeHead(201,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify(row))}catch(e){res.writeHead(422,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:e.message||'Draft save failed'}))}finally{await repo.close()}
  }
  if(process.env.CRM_DB_READ_ENABLED==='true'&&mode==='protected'&&principal&&p.match(/^\/api\/drafts\/[^/]+\/preflight$/)&&req.method==='GET'){const id=decodeURIComponent(p.split('/')[3]);const repo=createCrmRepository();try{const draft=await repo.getDraftById(id);if(!draft){res.writeHead(404,security);return res.end('Draft not found')}const workspace=await repo.getLeadWorkspace(draft.lead_id);res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify(draftPreflight({draft,workspace})))}finally{await repo.close()}}
  if(process.env.CRM_DB_WRITE_ENABLED==='true'&&mode==='protected'&&principal&&p.match(/^\/api\/drafts\/[^/]+\/status$/)&&req.method==='POST'){
   const id=decodeURIComponent(p.split('/')[3]);const body=await readJsonBody(req);const repo=createCrmRepository();try{const row=await repo.updateDraftStatus({id,status:String(body.status||''),actor:principal.user});if(!row){res.writeHead(404,security);return res.end('Draft not found')}res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify(row))}catch(e){res.writeHead(422,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:e.message||'Draft status update failed'}))}finally{await repo.close()}
  }

  // Read-only database pilot: explicit opt-in, protected access and no customer writes.
  if(p==='/api/db/status'||p==='/api/db/stats'||p==='/api/db/leads'||p.startsWith('/api/db/leads/')){
   if(process.env.CRM_DB_READ_ENABLED!=='true'||!process.env.DATABASE_URL||mode!=='protected'){
    res.writeHead(404,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:'Database pilot disabled'}));
   }
   if(req.method!=='GET'){res.writeHead(405,security);return res.end('Method not allowed');}
   const repo=createCrmRepository();
   try{
    const q=new URL(req.url,'http://localhost').searchParams;
    let data;
    if(p==='/api/db/status')data={connected:await repo.health(),readOnly:true};
    else if(p==='/api/db/stats'){
     data=await repo.dashboardStats(q.get('source_number')||'+919148338801');
    }
    else if(p==='/api/db/leads'){
     const raw=q.get('limit')??'50',offset=q.get('offset')??'0',sourceNumber=q.get('source_number')||'+919148338801',leadSort=q.get('lead_sort')||'last_message_desc',leadSearch=q.get('lead_search')||'';
     if(!/^\d{1,3}$/.test(raw)||!/^\d{1,7}$/.test(offset)){res.writeHead(400,security);return res.end('Invalid pagination');}
     if(leadSearch.length>200){res.writeHead(400,security);return res.end('Invalid lead search');}
     data=await repo.listLeadsPage(Number(raw),Number(offset),sourceNumber,q.get('lead_status')||'',leadSort,leadSearch);
    }else if(/^\/api\/db\/leads\/[^/]+\/workspace$/.test(p)){
     const id=decodeURIComponent(p.slice('/api/db/leads/'.length,-'/workspace'.length));
     if(!id||id.includes('/')||id.length>128){res.writeHead(400,security);return res.end('Invalid lead ID');}
     data=await repo.getLeadWorkspace(id,q.get('source_number')||'+919148338801');
     if(!data.lead){res.writeHead(404,security);return res.end('Lead not found');}
    }else{
     const id=decodeURIComponent(p.slice('/api/db/leads/'.length));
     if(!id||id.includes('/')||id.length>128){res.writeHead(400,security);return res.end('Invalid lead ID');}
     data=await repo.getLead(id);
     if(!data){res.writeHead(404,security);return res.end('Lead not found');}
    }
    res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify(data));
   }finally{await repo.close();}
  }
  if(p==='/api/inventory/overview'){
   if(process.env.CRM_DB_READ_ENABLED!=='true'||!process.env.DATABASE_URL||mode!=='protected'){res.writeHead(404,security);return res.end('Inventory unavailable');}
   if(req.method!=='GET'){res.writeHead(405,security);return res.end('Method not allowed');}
   const sortRaw=new URL(req.url,'http://localhost').searchParams.get('inventory_sort')||'latest';
   const sort=normalizeInventorySort(sortRaw);
   if(sortRaw!==sort){res.writeHead(400,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:'Invalid inventory sort',allowed:['latest','oldest','rent_asc','rent_desc','bhk_asc','bhk_desc','locality_asc']}));}
   const repo=createCrmRepository();
   try{const data=await repo.inventoryOverview();data.rows=sortInventoryRows(data.rows,sort);data.sort=sort;res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify(data))}
   finally{await repo.close()}
  }
  if(p==='/api/inventory/matches'){
   if(process.env.CRM_DB_READ_ENABLED!=='true'||!process.env.DATABASE_URL||mode!=='protected'){res.writeHead(404,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:'Inventory database disabled'}));}
   if(req.method!=='GET'){res.writeHead(405,security);return res.end('Method not allowed');}
   const q=new URL(req.url,'http://localhost').searchParams;
   const budgetRaw=q.get('budget');const limitRaw=q.get('limit')||'50';
   if(budgetRaw!==null&&!/^\d+(?:\.\d{1,2})?$/.test(budgetRaw)||!/^\d{1,3}$/.test(limitRaw)){res.writeHead(400,security);return res.end('Invalid inventory query');}
   const repo=createCrmRepository();try{const rows=await repo.matchInventory({bhk:q.get('bhk')||'',budget:budgetRaw===null?null:Number(budgetRaw),locality:q.get('locality')||'',furnishing:q.get('furnishing')||'',petFriendly:q.get('pet_friendly')||'',limit:Number(limitRaw)});res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({rows}));}finally{await repo.close()}
  }
  if(p==='/api/ai/analyze'){res.writeHead(404,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:'Retired API'}));}

  if(p==='/api/ai/analyze-real'&&req.method==='POST'){
   if(mode!=='protected'||process.env.CRM_REAL_AI_ENABLED!=='true'||process.env.CRM_DB_WRITE_ENABLED!=='true'){res.writeHead(403,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:'Real AI production mode is not enabled'}));}
   const repo=createCrmRepository();
   try{
    const body=await readJsonBody(req,8192);const id=String(body.leadId||'');const workspace=await repo.getLeadWorkspace(id);
    if(!workspace.lead){res.writeHead(404,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:'Lead not found'}));}
    const result=await analyzeRealLead({lead:workspace.lead,requirements:workspace.requirement_profile,messages:workspace.messages,aiHistory:workspace.ai_runs,cursor:workspace.ai_cursor,evidence:workspace.requirement_evidence,env:process.env});
    const run=await repo.saveAiRun({leadId:id,modelName:result.model,provider:result.provider,fallbackFrom:result.fallbackFrom||null,fallbackReason:result.fallbackReason||null,proposal:result.proposal,usage:result.usage||{}});
    const last=workspace.messages.at(-1);if(last)await repo.setAiCursor({leadId:id,sourceNumber:workspace.sources[0]?.source_number||'+919148338801',lastMessageId:last.id,lastMessageAt:last.message_at});
    const resolveMessageRef=ref=>{const key=String(ref??'').trim();if(!key)return null;const match=workspace.messages.find(m=>String(m.id)===key||String(m.source_message_id||m.provider_message_id||'')===key);return match?.id??null;};
    let draft=null;if(typeof result.proposal.reply_draft==='string'&&result.proposal.reply_draft.trim()){const rawEvidence=[...(Array.isArray(result.proposal.evidence)?result.proposal.evidence.map(x=>x?.message_id):[]),...(Array.isArray(result.proposal.requirement_updates)?result.proposal.requirement_updates.flatMap(x=>Array.isArray(x?.source_message_ids)?x.source_message_ids:[]):[])];const evidenceIds=[...new Set(rawEvidence.map(resolveMessageRef).filter(Number.isInteger))];draft=await repo.saveDraft({leadId:id,body:result.proposal.reply_draft,actor:principal.user,aiRunId:run.id,aiProvider:result.provider,modelName:result.model,evidenceMessageIds:evidenceIds,evidenceSummary:Array.isArray(result.proposal.evidence)?result.proposal.evidence.map(x=>String(x?.body||'')).filter(Boolean).slice(0,3).join(' | '):''});}
    res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({...result,run,draft}));
   }catch(e){res.writeHead(422,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:e.message==='Request too large'?'Request too large':'Real AI request failed'}));}
   finally{await repo.close()}
  }

  if(!['GET','HEAD'].includes(req.method)){res.writeHead(405,security);return res.end('Method not allowed');}
  if(p.startsWith('/api/')){res.writeHead(404,security);return res.end('API not enabled');}
  let f=resolve(join(root,p));
  if(!f.startsWith(root+'/')&&f!==root){res.writeHead(403,security);return res.end('Forbidden');}
  let info=await stat(f).catch(()=>null);
  if(!info||!info.isFile()){if(extname(p)){res.writeHead(404,security);return res.end('Not found');}f=join(root,'index.html');}
  const data=await readFile(f);
  res.writeHead(200,{...security,'Content-Type':mime[extname(f)]||'application/octet-stream'});return res.end(req.method==='HEAD'?undefined:data);
 }catch{res.writeHead(500,security);res.end('CRM unavailable');}
}).listen(Number(process.env.PORT||10000),'0.0.0.0',()=>{void startupDatabaseCheck(process.env);});