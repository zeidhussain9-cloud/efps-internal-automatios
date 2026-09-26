import pg from 'pg';
const SUPABASE_SESSION_POOLER_HOST='aws-0-ap-south-1.pooler.supabase.com';
const trimConnectionString=value=>{
 if(typeof value!=='string')return value;
 const trimmed=value.trim();
 if((trimmed.startsWith('"')&&trimmed.endsWith('"'))||(trimmed.startsWith("'")&&trimmed.endsWith("'")))return trimmed.slice(1,-1).trim();
 return trimmed;
};
const decodePart=value=>{try{return decodeURIComponent(value)}catch{return value}};
const encodePart=value=>encodeURIComponent(decodePart(value));
function parseLoosePostgresUrl(value){
 const trimmed=trimConnectionString(value);
 if(!/^postgres(?:ql)?:\/\//i.test(trimmed))return null;
 const body=trimmed.slice(trimmed.indexOf('://')+3);
 const at=body.lastIndexOf('@');
 if(at<=0)return null;
 const userInfo=body.slice(0,at);
 const remainder=body.slice(at+1);
 const colon=userInfo.indexOf(':');
 const username=colon>=0?userInfo.slice(0,colon):userInfo;
 const password=colon>=0?userInfo.slice(colon+1):'';
 const cutCandidates=[remainder.indexOf('/'),remainder.indexOf('?')].filter(n=>n>=0);
 const cut=cutCandidates.length?Math.min(...cutCandidates):-1;
 const authority=cut>=0?remainder.slice(0,cut):remainder;
 const pathAndQuery=cut>=0?remainder.slice(cut):'/postgres';
 const hostMatch=authority.match(/^([^:]+)(?::(\d+))?$/);
 if(!hostMatch)return null;
 return {hostname:hostMatch[1],port:hostMatch[2]||'',username,password,pathAndQuery};
}
function parseWhatwg(value){
 try{
  const url=new URL(trimConnectionString(value));
  if(/^postgres(?:ql)?$/i.test(url.protocol.replace(':',''))&&url.hostname)return {
   hostname:url.hostname,port:url.port,username:url.username,password:url.password,pathAndQuery:url.pathname+(url.search||'')
  };
 }catch{}
 return null;
}
function recognizedParts(value){
 const whatwg=parseWhatwg(value);
 if(whatwg&&(
   /^db\.[a-z0-9]+\.supabase\.co$/i.test(whatwg.hostname)||
   /^aws-[0-9-]+-[a-z0-9-]+\.pooler\.supabase\.com$/i.test(whatwg.hostname)
 ))return whatwg;
 return parseLoosePostgresUrl(value);
}
function stripConnectionOptions(pathAndQuery){
 const [path,query='']=pathAndQuery.split('?');
 const params=new URLSearchParams(query);
 params.delete('sslmode');
 return params.toString()?path+'?'+params.toString():path;
}
export function normalizeConnectionString(value){
 if(!value)return value;
 const parts=recognizedParts(value);
 if(!parts)return value;
 const direct=parts.hostname.match(/^db\.([a-z0-9]+)\.supabase\.co$/i);
 const pooler=parts.hostname.match(/^aws-[0-9-]+-([a-z0-9-]+)\.pooler\.supabase\.com$/i);
 if(direct){
  return 'postgresql://postgres.'+direct[1]+':'+encodePart(parts.password)+'@'+SUPABASE_SESSION_POOLER_HOST+':5432/postgres';
 }
 if(pooler&&parts.port==='5432'){
  const projectRef=parts.username.match(/^postgres\.([a-z0-9]+)$/i)?.[1];
  if(projectRef){
   return 'postgresql://postgres.'+projectRef+':'+encodePart(parts.password)+'@'+SUPABASE_SESSION_POOLER_HOST+':5432/postgres';
  }
 }
 return value;
}
export function connectionStringShape(value){
 const raw=typeof value==='string'?value.trim():'';
 const unquoted=trimConnectionString(value)||'';
 const parts=parseWhatwg(unquoted)||parseLoosePostgresUrl(unquoted);
 const host=parts?.hostname||'';
 const hostClass=/^db\.[a-z0-9]+\.supabase\.co$/i.test(host)?'supabase_direct':/^aws-[0-9-]+-[a-z0-9-]+\.pooler\.supabase\.com$/i.test(host)?'supabase_pooler':'other';
 return {
  present:Boolean(raw),
  length:raw.length,
  outerQuotes:Boolean(raw.length>=2&&((raw.startsWith('"')&&raw.endsWith('"'))||(raw.startsWith("'")&&raw.endsWith("'")))),
  postgresScheme:/^postgres(?:ql)?:\/\//i.test(unquoted),
  hasUserInfoAt:unquoted.includes('@'),
  parsed:Boolean(parts),
  hostClass,
  port:parts?.port||'default',
  usernamePresent:Boolean(parts?.username),
  passwordPresent:Boolean(parts?.password),
  databasePathPresent:Boolean(parts?.pathAndQuery),
  sslCaConfigured:Boolean(process.env.DATABASE_SSL_CA)
 };
}
export function connectionEndpointClass(value){
 if(!value)return 'missing';
 const normalized=normalizeConnectionString(value);
 const parts=parseWhatwg(normalized)||parseLoosePostgresUrl(normalized);
 if(!parts)return 'invalid_url';
 if(parts.hostname===SUPABASE_SESSION_POOLER_HOST&&parts.port==='5432')return 'supabase_session_pooler_ipv4';
 if(/^db\.[a-z0-9]+\.supabase\.co$/i.test(parts.hostname))return 'supabase_direct_ipv6_or_addon';
 if(/\.pooler\.supabase\.com$/i.test(parts.hostname))return 'supabase_pooler_other';
 return 'external_or_unknown';
}
export function createCrmRepository({pool,connectionString=process.env.DATABASE_URL,sslCa=process.env.DATABASE_SSL_CA}={}){
 if(!pool&&!connectionString)throw Error('DATABASE_URL required');
 const db=pool||new pg.Pool({connectionString:normalizeConnectionString(connectionString),max:5,connectionTimeoutMillis:5000,ssl:{rejectUnauthorized:true,...(sslCa?{ca:sslCa}: {})}});
 return {
  async health(){const r=await db.query('SELECT 1 AS ok');return r.rows[0]?.ok===1;},
  async listLeads(limit=50){if(!Number.isInteger(limit)||limit<1||limit>100)throw Error('Invalid limit');const r=await db.query('SELECT id,display_name,status,priority,requirements,updated_at FROM crm_leads ORDER BY updated_at DESC,id LIMIT $1',[limit]);return r.rows;},
  async getLead(id){if(typeof id!=='string'||!id||id.length>128)throw Error('Invalid lead ID');const r=await db.query('SELECT * FROM crm_leads WHERE id=$1',[id]);return r.rows[0]||null;},
  async close(){if(!pool)await db.end();}
 };
}
