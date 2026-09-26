// Explicit operator-run migration only. Never invoked from the web server or deployment build.
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
export function migrationGuard(env){if(env.CRM_MIGRATION_APPROVED!=='true')throw Error('Explicit CRM_MIGRATION_APPROVED=true required');if(!env.DATABASE_URL)throw Error('DATABASE_URL required');if(env.CRM_REAL_DATA_ENABLED==='true')throw Error('Disable live data ingestion during migration');}
export async function runMigration({env=process.env,read=readFile,connect}={}){
 migrationGuard(env);
 if(typeof connect!=='function')throw Error('Database connector required');
 const sql=await read(resolve(dirname(fileURLToPath(import.meta.url)),'../db/migrations/001_crm_core.sql'),'utf8');
 if(!sql.includes('BEGIN;')||!sql.includes('COMMIT;'))throw Error('Migration transaction markers missing');
 const db=await connect(env.DATABASE_URL);
 try{await db.query(sql);return{version:1,applied:true}}finally{await db.end()}
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const{Client}=await import('pg');
 try{const result=await runMigration({connect:async url=>{const client=new Client({connectionString:url,ssl:url.includes('localhost')?false:{rejectUnauthorized:true}});await client.connect();return client}});console.log('CRM schema migration applied:',result.version)}
 catch(e){console.error('CRM migration failed:',e.message);process.exitCode=1}
}
