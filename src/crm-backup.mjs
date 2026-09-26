import {createCipheriv,createDecipheriv,randomBytes} from 'node:crypto';

const MAGIC='EFPS_CRM_BACKUP_V1';
export function decodeBackupKey(value){
 if(typeof value!=='string'||!value)return null;
 try{const key=Buffer.from(value,'base64');return key.length===32?key:null}catch{return null}
}
export function encryptBackup(data,key){
 if(!Buffer.isBuffer(data)||!Buffer.isBuffer(key)||key.length!==32)throw Error('Invalid backup key');
 const iv=randomBytes(12),cipher=createCipheriv('aes-256-gcm',key,iv);
 const ciphertext=Buffer.concat([cipher.update(data),cipher.final()]),tag=cipher.getAuthTag();
 return Buffer.from(JSON.stringify({magic:MAGIC,iv:iv.toString('base64'),tag:tag.toString('base64'),data:ciphertext.toString('base64')})+'\n','utf8');
}
export function decryptBackup(payload,key){
 if(!Buffer.isBuffer(payload)||!Buffer.isBuffer(key)||key.length!==32)throw Error('Invalid backup key');
 let doc;try{doc=JSON.parse(payload.toString('utf8'))}catch{throw Error('Invalid backup envelope')}
 if(doc.magic!==MAGIC)throw Error('Unsupported backup format');
 const iv=Buffer.from(doc.iv,'base64'),tag=Buffer.from(doc.tag,'base64'),data=Buffer.from(doc.data,'base64');
 if(iv.length!==12||tag.length!==16||!data.length)throw Error('Invalid backup envelope');
 const decipher=createDecipheriv('aes-256-gcm',key,iv);decipher.setAuthTag(tag);
 try{return Buffer.concat([decipher.update(data),decipher.final()])}catch{throw Error('Backup authentication failed')}
}
export function assertBackupEnvironment(env){
 if(!env.DATABASE_URL)throw Error('DATABASE_URL required');
 if(!env.DATABASE_SSL_CA)throw Error('DATABASE_SSL_CA required');
 const key=decodeBackupKey(env.CRM_BACKUP_KEY);if(!key)throw Error('CRM_BACKUP_KEY must be base64-encoded 32 bytes');
 return key;
}
export function assertRestoreApproved(env){if(env.CRM_RESTORE_APPROVED!=='true')throw Error('Explicit CRM_RESTORE_APPROVED=true required')}
