import pg from 'pg';
// Server-only repository; never bundle into the browser.
export function createCrmRepository({pool,connectionString=process.env.DATABASE_URL}={}) {
 if (!pool && !connectionString) throw Error('DATABASE_URL required');
 const db=pool||new pg.Pool({connectionString,max:5,connectionTimeoutMillis:5000});
 return {
  async health(){const r=await db.query('SELECT 1 AS ok');return r.rows[0]?.ok===1;},
  async listLeads(limit=50){if(!Number.isInteger(limit)||limit<1||limit>100)throw Error('Invalid limit');const r=await db.query('SELECT id,display_name,status,priority,requirements,updated_at FROM crm_leads ORDER BY updated_at DESC,id LIMIT $1',[limit]);return r.rows;},
  async getLead(id){if(typeof id!=='string'||!id||id.length>128)throw Error('Invalid lead ID');const r=await db.query('SELECT * FROM crm_leads WHERE id=$1',[id]);return r.rows[0]||null;},
  async close(){if(!pool)await db.end();}
 };
}
