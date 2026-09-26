// Explicit operator-run migration only. Never invoked from the web server or deployment build.
import {readFile,readdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {dirname,resolve,basename} from 'node:path';
import {Client} from 'pg';
import {normalizeConnectionString} from '../src/crm-repository.mjs';

export function migrationGuard(env){
 if(env.CRM_MIGRATION_APPROVED!=='true')throw Error('Explicit CRM_MIGRATION_APPROVED=true required');
 if(!env.DATABASE_URL)throw Error('DATABASE_URL required');
 if(env.CRM_REAL_DATA_ENABLED==='true')throw Error('Disable live data ingestion during migration');
}

export async function listMigrationFiles({dir=resolve(dirname(fileURLToPath(import.meta.url)),'../db/migrations'),list=readdir}={}){
 const names=(await list(dir)).filter(name=>/^\d+_.*\.sql$/.test(name)).sort((a,b)=>Number(a.split('_')[0])-Number(b.split('_')[0]));
 if(!names.length)throw Error('No CRM migrations found');
 return names;
}

export async function runMigration({env=process.env,read=readFile,connect,dir}={}){
 migrationGuard(env);
 if(typeof connect!=='function')throw Error('Database connector required');
 const db=await connect({connectionString:normalizeConnectionString(env.DATABASE_URL),sslCa:env.DATABASE_SSL_CA});
 try{
  await db.query('CREATE TABLE IF NOT EXISTS crm_schema_migrations(version integer PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())');
  for(const file of await listMigrationFiles({dir})){
   const version=Number(file.split('_')[0]);
   const exists=await db.query('SELECT 1 FROM crm_schema_migrations WHERE version=$1',[version]);
   if(exists.rows[0])continue;
   const sql=await read(resolve(dir,file),'utf8');
   if(!sql.includes('BEGIN;')||!sql.includes('COMMIT;'))throw Error('Migration transaction markers missing: '+file);
   await db.query(sql);
   await db.query('INSERT INTO crm_schema_migrations(version) VALUES($1) ON CONFLICT DO NOTHING',[version]);
  }
  return{applied:true};
 }finally{await db.end()}
}

if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 try{
  const result=await runMigration({connect:async({connectionString,sslCa})=>{
   const client=new Client({connectionString,ssl:{rejectUnauthorized:true,...(sslCa?{ca:sslCa}:{})}});
   await client.connect();return client;
  }});
  console.log('CRM schema migrations applied:',result.applied);
 }catch(e){console.error('CRM migration failed:',e.message);process.exitCode=1}
}
