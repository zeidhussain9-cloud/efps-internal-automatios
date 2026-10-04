import {McpServer} from '@modelcontextprotocol/sdk/server/mcp.js';
import {StreamableHTTPServerTransport} from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import {z} from 'zod/v4';
import {timingSafeEqual,createPublicKey,verify as verifySignature} from 'node:crypto';
import {sourceAuditSnapshot,whapiHealth,whapiRecentMessages,whapiMessage,housingSheetSnapshot} from './src/crm-source-audit.mjs';

const TOKEN=String(process.env.CRM_SOURCE_AUDIT_TOKEN||'').trim();
const enabled=process.env.CRM_SOURCE_AUDIT_MCP_ENABLED==='true';
const OIDC_ISSUER='https://token.actions.githubusercontent.com';
const OIDC_AUDIENCE='efps-crm-source-audit';
const OIDC_JWKS_URL=OIDC_ISSUER+'/.well-known/jwks';
const OIDC_REPOSITORY='zeidhussain9-cloud/efps-internal-automatios';
const OIDC_REF='refs/heads/main';
const OIDC_WORKFLOW_REF=OIDC_REPOSITORY+'/.github/workflows/crm-source-audit-schedule.yml@'+OIDC_REF;
let jwksCache=null;

function staticAuthorized(req){
  if(!TOKEN)return false;
  const got=String(req.headers.authorization||'').replace(/^Bearer\s+/i,'');
  const a=Buffer.from(TOKEN),b=Buffer.from(got);
  return a.length===b.length&&timingSafeEqual(a,b);
}

function decodeJwtPart(value){
  return JSON.parse(Buffer.from(value,'base64url').toString('utf8'));
}

async function oidcAuthorized(req){
  const raw=String(req.headers.authorization||'').replace(/^Bearer\s+/i,'').trim();
  if(!raw||raw.split('.').length!==3)return false;
  try{
    const [encodedHeader,encodedPayload,encodedSignature]=raw.split('.');
    const header=decodeJwtPart(encodedHeader);
    const claims=decodeJwtPart(encodedPayload);
    if(header.alg!=='RS256'||!header.kid)return false;
    if(claims.iss!==OIDC_ISSUER||claims.aud!==OIDC_AUDIENCE||claims.repository!==OIDC_REPOSITORY||claims.ref!==OIDC_REF||claims.workflow_ref!==OIDC_WORKFLOW_REF)return false;
    if(claims.repository_visibility!=='public'||claims.ref_type!=='branch')return false;
    const now=Math.floor(Date.now()/1000);
    if(!Number.isInteger(claims.exp)||claims.exp<now-30||!Number.isInteger(claims.nbf)||claims.nbf>now+30)return false;
    if(!jwksCache||jwksCache.expiresAt<now){
      const response=await fetch(OIDC_JWKS_URL);
      if(!response.ok)throw Error('OIDC JWKS unavailable');
      jwksCache={keys:(await response.json()).keys,expiresAt:now+300};
    }
    const jwk=jwksCache.keys.find(key=>key.kid===header.kid&&key.kty==='RSA');
    if(!jwk)return false;
    const key=createPublicKey({key:jwk,format:'jwk'});
    return verifySignature('RSA-SHA256',Buffer.from(encodedHeader+'.'+encodedPayload),key,Buffer.from(encodedSignature,'base64url'));
  }catch{return false}
}

async function authorized(req){
  return staticAuthorized(req)||await oidcAuthorized(req);
}

function server(){
  const s=new McpServer({name:'efps-crm-source-audit',version:'1.0.0'});
  s.registerTool('whapi_channel_health',{description:'Read-only WhAPI channel health.',inputSchema:{}},async()=>{
    return {content:[{type:'text',text:JSON.stringify(await whapiHealth())}]};
  });
  s.registerTool('whapi_recent_messages',{description:'Read-only recent inbound WhAPI messages for source reconciliation.',inputSchema:{count:z.number().int().min(1).max(100).default(100),timeFrom:z.number().optional(),timeTo:z.number().optional()}},async({count,timeFrom,timeTo})=>{
    return {content:[{type:'text',text:JSON.stringify(await whapiRecentMessages({count,fromMe:false,timeFrom,timeTo}))}]};
  });
  s.registerTool('whapi_message',{description:'Read-only full WhAPI message lookup by provider message ID.',inputSchema:{id:z.string().min(1).max(256)}},async({id})=>{
    return {content:[{type:'text',text:JSON.stringify(await whapiMessage(id))}]};
  });
  s.registerTool('google_housing_sheet_snapshot',{description:'Read-only canonical Housing_Listings Sheet snapshot.',inputSchema:{}},async()=>{
    return {content:[{type:'text',text:JSON.stringify(await housingSheetSnapshot())}]};
  });
  s.registerTool('crm_source_audit_snapshot',{description:'Read-only cross-source snapshot for WhAPI, Google Sheet and CRM persistence.',inputSchema:{}},async()=>{
    return {content:[{type:'text',text:JSON.stringify(await sourceAuditSnapshot())}]};
  });
  return s;
}

export async function handleAuditMcp(req,res){
  if(!enabled||!(await authorized(req))){res.writeHead(401,{'Content-Type':'application/json','Cache-Control':'no-store'});return res.end(JSON.stringify({error:'MCP authentication required'}));}
  if(req.method!=='POST'){res.writeHead(405,{'Allow':'POST','Cache-Control':'no-store'});return res.end('Method not allowed');}
  const s=server(); const transport=new StreamableHTTPServerTransport({sessionIdGenerator:undefined});
  try{await s.connect(transport);await transport.handleRequest(req,res);res.on('close',()=>{transport.close();s.close();});}
  catch(error){console.error('CRM source-audit MCP error',error?.message||error);if(!res.headersSent)res.writeHead(500,{'Content-Type':'application/json','Cache-Control':'no-store'});if(!res.writableEnded)res.end(JSON.stringify({error:'MCP request failed'}));}
}
