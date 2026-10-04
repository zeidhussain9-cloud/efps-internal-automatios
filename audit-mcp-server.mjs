import {McpServer} from '@modelcontextprotocol/sdk/server/mcp.js';
import {StreamableHTTPServerTransport} from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import {z} from 'zod/v4';
import {timingSafeEqual} from 'node:crypto';
import {sourceAuditSnapshot,whapiHealth,whapiRecentMessages,whapiMessage,housingSheetSnapshot} from './src/crm-source-audit.mjs';

const TOKEN=String(process.env.CRM_SOURCE_AUDIT_TOKEN||'').trim();
const enabled=process.env.CRM_SOURCE_AUDIT_MCP_ENABLED==='true';

function authorized(req){
  if(!TOKEN)return false;
  const got=String(req.headers.authorization||'').replace(/^Bearer\s+/i,'');
  const a=Buffer.from(TOKEN),b=Buffer.from(got);
  return a.length===b.length&&timingSafeEqual(a,b);
}
function server(){
  const s=new McpServer({name:'efps-crm-source-audit',version:'1.0.0'});
  s.registerTool('whapi_channel_health',{description:'Read-only WhAPI channel health.',inputSchema:{}},async()=>{
    return {content:[{type:'text',text:JSON.stringify(await whapiHealth())}]};
  });
  s.registerTool('whapi_recent_messages',{description:'Read-only recent inbound WhAPI messages for source reconciliation.',inputSchema:{count:z.number().int().min(1).max(100).default(100),timeFrom:z.number().optional(),timeTo:z.number().optional()}},async({count,timeFrom,timeTo})=>{
    return {content:[{type:'text',text:JSON.stringify(await whapiRecentMessages({count,fromMe:false,timeFrom,timeTo}))}]};
  });  s.registerTool('whapi_message',{description:'Read-only full WhAPI message lookup by provider message ID.',inputSchema:{id:z.string().min(1).max(256)}},async({id})=>{
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
  if(!enabled||!authorized(req)){res.writeHead(401,{'Content-Type':'application/json','Cache-Control':'no-store'});return res.end(JSON.stringify({error:'MCP authentication required'}));}
  if(req.method!=='POST'){res.writeHead(405,{'Allow':'POST','Cache-Control':'no-store'});return res.end('Method not allowed');}
  const s=server(); const transport=new StreamableHTTPServerTransport({sessionIdGenerator:undefined});
  try{await s.connect(transport);await transport.handleRequest(req,res);res.on('close',()=>{transport.close();s.close();});}
  catch(error){console.error('CRM source-audit MCP error',error?.message||error);if(!res.headersSent)res.writeHead(500,{'Content-Type':'application/json','Cache-Control':'no-store'});if(!res.writableEnded)res.end(JSON.stringify({error:'MCP request failed'}));}
}
