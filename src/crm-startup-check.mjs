// Startup-only diagnostics: report configuration presence and connection outcome, never secret values.
import {createCrmRepository,connectionEndpointClass} from './crm-repository.mjs';
export function configurationStatus(env){
 return {
  databaseUrlPresent:Boolean(env.DATABASE_URL),
  databaseReadOptIn:env.CRM_DB_READ_ENABLED==='true',
  authConfigured:Boolean(env.CRM_BASIC_AUTH_USERNAME&&env.CRM_BASIC_AUTH_PASSWORD),
  authIncomplete:Boolean(env.CRM_BASIC_AUTH_USERNAME)!==Boolean(env.CRM_BASIC_AUTH_PASSWORD),
  ollamaEndpointPresent:Boolean(env.OLLAMA_BASE_URL||env.OLLAMA_HOST),
  ollamaModelPresent:Boolean(env.OLLAMA_MODEL||env.OLLAMA_MODEL_NAME),
  sheetsCredentialPresent:Boolean(env.GOOGLE_SERVICE_ACCOUNT_JSON_BASE64||env.GOOGLE_SERVICE_ACCOUNT_JSON||env.GOOGLE_APPLICATION_CREDENTIALS),
  sheetsIdPresent:Boolean(env.HOUSING_SHEET_ID||env.SHEET_ID),
  liveDataEnabled:env.CRM_REAL_DATA_ENABLED==='true'
 };
}
export async function startupDatabaseCheck(env,{createRepository=createCrmRepository,log=console.info}={}){
 const flags=configurationStatus(env);
 // Never log the connection string, credentials, or raw exception.
 log('CRM configuration flags:',JSON.stringify(flags));
 log('CRM database endpoint class:',connectionEndpointClass(env.DATABASE_URL));
 if(!flags.databaseUrlPresent){log('CRM database connectivity: not configured');return 'not_configured';}
 let repo;
 try{
  repo=createRepository({connectionString:env.DATABASE_URL});
  const ok=await repo.health();
  log('CRM database connectivity:',ok?'connected':'failed');
  return ok?'connected':'failed';
 }catch(error){
  const code=error?.code;
  const category=code==='ENETUNREACH'||code==='EHOSTUNREACH'?'network':code==='ENOTFOUND'||code==='EAI_AGAIN'?'dns':code==='ETIMEDOUT'?'timeout':code==='ECONNREFUSED'?'refused':code==='28P01'?'authentication':code==='3D000'?'database':code==='42501'?'permission':'unknown';
  log('CRM database connectivity: failed (category: '+category+')');
  return 'failed';
 }finally{if(repo)try{await repo.close()}catch{}}
}
