import {createServer} from 'node:http';
import {readFile,stat} from 'node:fs/promises';
import {join,extname,resolve} from 'node:path';
import {authorized,accessMode} from './src/server-auth.mjs';
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
