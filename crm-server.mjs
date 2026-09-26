import {createServer} from 'node:http';
import {readFile,stat} from 'node:fs/promises';
import {join,extname,resolve} from 'node:path';
import {authorized,accessMode} from './src/server-auth.mjs';
import {analyzeFictionalLead} from './src/ollama-adapter.mjs';
import {createCrmRepository} from './src/crm-repository.mjs';
const root=resolve('dist');
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.ico':'image/x-icon'};
const security={'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Frame-Options':'DENY','Cache-Control':'no-store','Content-Security-Policy':"default-src 'self'; img-src 'self' https: data:; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"};
createServer(async(req,res)=>{
 try{
  const p=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
  if(p==='/health'){res.writeHead(200,{...security,'Content-Type':'application/json'});return res.end(JSON.stringify({ok:true,mode:'synthetic',access:accessMode(process.env)}));}
  const mode=accessMode(process.env);
  if(mode==='misconfigured'){res.writeHead(503,security);return res.end('CRM access configuration incomplete');}
  if(mode==='protected'&&!authorized(req.headers.authorization,process.env.CRM_BASIC_AUTH_USERNAME,process.env.CRM_BASIC_AUTH_PASSWORD)){res.writeHead(401,{...security,'WWW-Authenticate':'Basic realm="EasyFind CRM"'});return res.end('Authentication required');}
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
     if(!/^\\d{1,3}$/.test(raw)){res.writeHead(400,security);return res.end('Invalid limit');}
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
}).listen(Number(process.env.PORT||10000),'0.0.0.0');
