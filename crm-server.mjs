import {createServer} from 'node:http';
import {randomUUID,createHmac,timingSafeEqual} from 'node:crypto';
import {readFile,stat} from 'node:fs/promises';
import {join,extname,resolve} from 'node:path';
import {authorized,accessMode} from './src/server-auth.mjs';
import {analyzeFictionalLead} from './src/ollama-adapter.mjs';
import {createCrmRepository} from './src/crm-repository.mjs';
import {startupDatabaseCheck} from './src/crm-startup-check.mjs';
const root=resolve('dist');
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.ico':'image/x-icon'};
async function readJsonBody(req,maxBytes=16384){let raw='';for await(const chunk of req){raw+=chunk;if(Buffer.byteLength(raw,'utf8')>maxBytes)throw Object.assign(Error('Request too large'),{statusCode:413})}if(!raw.trim())return{};try{const value=JSON.parse(raw);if(!value||typeof value!=='object'||Array.isArray(value))throw Error('JSON object required');return value}catch{throw Object.assign(Error('Invalid JSON body'),{statusCode:400})}}
const security={'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Frame-Options':'DENY','Cache-Control':'no-store','Strict-Transport-Security':'max-age=31536000','Permissions-Policy':'geolocation=(),camera=(),microphone=()','Cross-Origin-Opener-Policy':'same-origin','Cross-Origin-Resource-Policy':'same-origin','X-Permitted-Cross-Domain-Policies':'none','Content-Security-Policy':"default-src 'self'; img-src 'self' https: data:; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"};
createServer(async(req,res)=>{
 try{
  const p=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
  if(p==='/health'){res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({ok:true}));}
  const mode=accessMode(process.env);
  if(mode==='misconfigured'){res.writeHead(503,security);return res.end('CRM access configuration incomplete');}
  if(mode==='protected'&&!authorized(req.headers.authorization,process.env.CRM_BASIC_AUTH_USERNAME,process.env.CRM_BASIC_AUTH_PASSWORD)){res.writeHead(401,{...security,'WWW-Authenticate':'Basic realm="EasyFind CRM"'});return res.end('Authentication required');}
  if(p==='/api/internal/inventory/sync'&&req.method==='POST'){
   if(process.env.CRM_INVENTORY_SYNC_ENABLED!=='true'||!process.env.CRM_INVENTORY_SYNC_SECRET){res.writeHead(404,security);return res.end('Inventory sync disabled');}
   const ts=String(req.headers['x-efps-inventory-timestamp']||'');const provided=String(req.headers['x-efps-inventory-signature']||'');
   if(!/^\\d+$/.test(ts)||Math.abs(Date.now()-Number(ts)*1000)>300000||!/^[a-f0-9]{64}$/i.test(provided)){res.writeHead(401,security);return res.end('Invalid inventory sync authentication');}
   const expected=createHmac('sha256',process.env.CRM_INVENTORY_SYNC_SECRET).update(ts).digest('hex');
   if(expected.length!==provided.length||!timingSafeEqual(Buffer.from(expected),Buffer.from(provided.toLowerCase()))){res.writeHead(401,security);return res.end('Invalid inventory sync authentication');}
   try{const {readCanonicalInventory,syncInventorySnapshot}=await import('./src/inventory-sync.mjs');const rows=await readCanonicalInventory(process.env);const result=await syncInventorySnapshot({rows});res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({ok:true,...result}));}
   catch(e){res.writeHead(502,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({ok:false,error:'Inventory sync failed'}));}
  }
  // Durable database writes: explicit opt-in, protected access and audited in the same transaction.
  if(process.env.CRM_DB_WRITE_ENABLED==='true'&&mode==='protected'&&req.method!=='GET'&&(p==='/api/db/leads'||p.startsWith('/api/db/leads/')||p==='/api/db/followups'||p.startsWith('/api/db/followups/'))){
   if(!process.env.DATABASE_URL){res.writeHead(404,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:'Database write pilot disabled'}));}
   const repo=createCrmRepository();const actor=process.env.CRM_BASIC_AUTH_USERNAME;
   try{
    if(p==='/api/db/leads'&&req.method==='POST'){
     const body=await readJsonBody(req);const lead=await repo.createLead({id:body.id,displayName:body.displayName,normalizedPhone:body.normalizedPhone,status:body.status,priority:body.priority,requirements:body.requirements,operatorNotes:body.operatorNotes,actor});res.writeHead(201,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify(lead));
    }
    if(p.startsWith('/api/db/leads/')&&req.method==='PATCH'){
     const id=decodeURIComponent(p.slice('/api/db/leads/'.length));if(!id||id.includes('/')||id.length>128){res.writeHead(400,security);return res.end('Invalid lead ID')}
     const body=await readJsonBody(req);const lead=await repo.updateLead({id,displayName:body.displayName,normalizedPhone:body.normalizedPhone,status:body.status,priority:body.priority,requirements:body.requirements,operatorNotes:body.operatorNotes,actor});if(!lead){res.writeHead(404,security);return res.end('Lead not found')}res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify(lead));
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
  // Read-only database pilot: explicit opt-in, protected access and no customer writes.
  if(p==='/api/db/status'||p==='/api/db/leads'||p.startsWith('/api/db/leads/')){
   if(process.env.CRM_DB_READ_ENABLED!=='true'||!process.env.DATABASE_URL||mode!=='protected'){
    res.writeHead(404,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:'Database pilot disabled'}));
   }
   if(req.method!=='GET'){res.writeHead(405,security);return res.end('Method not allowed');}
   const repo=createCrmRepository();
   try{
    let data;
    if(p==='/api/db/status')data={connected:await repo.health(),readOnly:true};
    else if(p==='/api/db/leads'){
     const q=new URL(req.url,'http://localhost').searchParams;
     const raw=q.get('limit')??'50';
     if(!/^\d{1,3}$/.test(raw)){res.writeHead(400,security);return res.end('Invalid limit');}
     data={leads:await repo.listLeads(Number(raw))};
    }else{
     const id=decodeURIComponent(p.slice('/api/db/leads/'.length));
     if(!id||id.includes('/')||id.length>128){res.writeHead(400,security);return res.end('Invalid lead ID');}
     data=await repo.getLead(id);
     if(!data){res.writeHead(404,security);return res.end('Lead not found');}
    }
    res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify(data));
   }finally{await repo.close();}
  }
  if(p==='/api/inventory/matches'){
   if(process.env.CRM_DB_READ_ENABLED!=='true'||!process.env.DATABASE_URL||mode!=='protected'){res.writeHead(404,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:'Inventory database disabled'}));}
   if(req.method!=='GET'){res.writeHead(405,security);return res.end('Method not allowed');}
   const q=new URL(req.url,'http://localhost').searchParams;
   const budgetRaw=q.get('budget');const limitRaw=q.get('limit')||'50';
   if(budgetRaw!==null&&!/^\\d+(?:\\.\\d{1,2})?$/.test(budgetRaw)||!/^\\d{1,3}$/.test(limitRaw)){res.writeHead(400,security);return res.end('Invalid inventory query');}
   const repo=createCrmRepository();try{const rows=await repo.matchInventory({bhk:q.get('bhk')||'',budget:budgetRaw===null?null:Number(budgetRaw),locality:q.get('locality')||'',furnishing:q.get('furnishing')||'',petFriendly:q.get('pet_friendly')||'',limit:Number(limitRaw)});res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({rows}));}finally{await repo.close()}
  }
  if(p==='/api/ai/analyze'&&req.method==='POST'){
   if(mode!=='protected'||process.env.CRM_SYNTHETIC_AI_ENABLED!=='true'){res.writeHead(403,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:'Synthetic AI disabled'}));}
   try{
    let raw='';for await(const chunk of req){raw+=chunk;if(raw.length>1024)throw Error('Request too large');}
    const body=JSON.parse(raw);const result=await analyzeFictionalLead({leadId:body.leadId,env:process.env});
    res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify(result));
   }catch(e){res.writeHead(422,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({error:e.message==='Unknown fictional lead'?e.message:'Synthetic AI request failed'}));}
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
