import pg from 'pg';
const SUPABASE_SESSION_POOLER_HOST='aws-0-ap-south-1.pooler.supabase.com';
// Server-only repository. Prefer the IPv4-compatible Supabase Session Pooler for this
// persistent Render service when the configured URL points at a Supabase endpoint.
export function normalizeConnectionString(value){
 if(!value)return value;
 try{
  const url=new URL(value);
  const direct=url.hostname.match(/^db\.([a-z0-9]+)\.supabase\.co$/i);
  const pooler=url.hostname.match(/^aws-[0-9-]+-([a-z0-9-]+)\.pooler\.supabase\.com$/i);
  if(direct){
   url.hostname=SUPABASE_SESSION_POOLER_HOST;
   url.port='5432';
   if(url.username==='postgres')url.username='postgres.'+direct[1];
   if(!url.searchParams.has('sslmode'))url.searchParams.set('sslmode','require');
   return url.toString();
  }
  if(pooler&&url.port==='5432'){
   const projectRef=(url.username||'').match(/^postgres\.([a-z0-9]+)$/i)?.[1];
   if(projectRef){
    url.hostname=SUPABASE_SESSION_POOLER_HOST;
    url.username='postgres.'+projectRef;
    if(!url.searchParams.has('sslmode'))url.searchParams.set('sslmode','require');
    return url.toString();
   }
  }
  return value;
 }catch{return value;}
}
export function connectionEndpointClass(value){
 if(!value)return 'missing';
 try{
  const url=new URL(normalizeConnectionString(value));
  if(url.hostname===SUPABASE_SESSION_POOLER_HOST&&url.port==='5432')return 'supabase_session_pooler_ipv4';
  if(/^db\.[a-z0-9]+\.supabase\.co$/i.test(url.hostname))return 'supabase_direct_ipv6_or_addon';
  if(/\.pooler\.supabase\.com$/i.test(url.hostname))return 'supabase_pooler_other';
  return 'external_or_unknown';
 }catch{return 'invalid_url';}
}
export function createCrmRepository({pool,connectionString=process.env.DATABASE_URL}={}){
 if(!pool&&!connectionString)throw Error('DATABASE_URL required');
 const db=pool||new pg.Pool({connectionString:normalizeConnectionString(connectionString),max:5,connectionTimeoutMillis:5000});
 return {
  async health(){const r=await db.query('SELECT 1 AS ok');return r.rows[0]?.ok===1;},
  async listLeads(limit=50){if(!Number.isInteger(limit)||limit<1||limit>100)throw Error('Invalid limit');const r=await db.query('SELECT id,display_name,status,priority,requirements,updated_at FROM crm_leads ORDER BY updated_at DESC,id LIMIT $1',[limit]);return r.rows;},
  async getLead(id){if(typeof id!=='string'||!id||id.length>128)throw Error('Invalid lead ID');const r=await db.query('SELECT * FROM crm_leads WHERE id=$1',[id]);return r.rows[0]||null;},
  async close(){if(!pool)await db.end();}
 };
}
