import {spawn} from 'node:child_process';
import {mkdtemp,rm,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';
import {assertBackupEnvironment,encryptBackup} from '../src/crm-backup.mjs';
import {normalizeConnectionString} from '../src/crm-repository.mjs';

function connectionEnv(url,ca){const u=new URL(normalizeConnectionString(url));return{PGHOST:u.hostname,PGPORT:u.port||'5432',PGDATABASE:decodeURIComponent(u.pathname.slice(1)||'postgres'),PGUSER:decodeURIComponent(u.username),PGPASSWORD:u.password,PGSSLMODE:'verify-full',PGSSLROOTCERT:ca}}
function runDump({url,ca}){return new Promise((resolvePromise,reject)=>{const child=spawn('pg_dump',['--format=custom','--no-owner','--no-privileges'],{env:{...process.env,...connectionEnv(url,ca)},stdio:['ignore','pipe','ignore']});const chunks=[];child.on('error',reject);child.stdout.on('data',chunk=>chunks.push(chunk));child.on('close',code=>code===0?resolvePromise(Buffer.concat(chunks)):reject(Error('pg_dump failed')));})}

if(import.meta.url===new URL(process.argv[1],'file:').href){
 try{
  const key=assertBackupEnvironment(process.env);
  const stamp=new Date().toISOString().replace(/[:.]/g,'-');
  const output=resolve(process.env.CRM_BACKUP_OUTPUT||('crm-backup-'+stamp+'.enc'));
  const work=await mkdtemp(resolve(tmpdir(),'efps-crm-backup-'));
  const caPath=resolve(work,'ca.crt');
  await writeFile(caPath,process.env.DATABASE_SSL_CA,{mode:0o600});
  try{
   const dump=await runDump({url:process.env.DATABASE_URL,ca:caPath});
   const encrypted=encryptBackup(dump,key);
   await writeFile(output,encrypted,{mode:0o600});
   console.log('CRM encrypted backup written:',output);
  }finally{await rm(work,{recursive:true,force:true})}
 }catch(e){console.error('CRM backup failed:',e.message);process.exitCode=1}
}