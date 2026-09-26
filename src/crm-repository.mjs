import pg from 'pg';
const SUPABASE_SESSION_POOLER_HOST='aws-0-ap-south-1.pooler.supabase.com';
// Server-only repository. When the configured Supabase URL is the direct IPv6 endpoint,
// transparently use the IPv4-compatible Session Pooler for the Render backend.
export function normalizeConnectionString(value){
 if(!value) return value;
 try{
  const url=new URL(value);
  const match=url.hostname.match(/^db\.([a-z0-9]+)\.supabase\.co$/i);
  if(!match)return value;
  url.hostname=SUPABASE_SESSION_POOLER_HOST;
  url.port='5432';
  if(url.username==='postgres')url.username='postgres.'+match[1];
  if(!url.searchParams.has('sslmode'))url.searchParams.set('sslmode','require');
  return url.toString();
 }catch{return value;}
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
