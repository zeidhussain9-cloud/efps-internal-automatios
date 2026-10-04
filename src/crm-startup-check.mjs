// Startup-only diagnostics: report configuration presence and connection outcome, never secret values.
import {createCrmRepository,connectionEndpointClass,connectionStringShape} from './crm-repository.mjs';
export function configurationStatus(env){
 return {
  databaseUrlPresent:Boolean(env.DATABASE_URL),
  databaseReadOptIn:env.CRM_DB_READ_ENABLED==='true',
  databaseWriteOptIn:env.CRM_DB_WRITE_ENABLED==='true',
  databaseTlsCaPresent:Boolean(env.DATABASE_SSL_CA),
  authConfigured:Boolean(env.CRM_BASIC_AUTH_USERNAME&&env.CRM_BASIC_AUTH_PASSWORD),
  authIncomplete:Boolean(env.CRM_BASIC_AUTH_USERNAME)!==Boolean(env.CRM_BASIC_AUTH_PASSWORD),
  ollamaEndpointPresent:Boolean(env.OLLAMA_BASE_URL||env.OLLAMA_HOST),
  ollamaModelPresent:Boolean(env.OLLAMA_MODEL||env.OLLAMA_MODEL_NAME),
  ollamaApiKeyPresent:Boolean(env.OLLAMA_API_KEY),
  bedrockRegionPresent:Boolean(env.AWS_REGION||env.AWS_DEFAULT_REGION),
  bedrockModelPresent:Boolean(env.AWS_BEDROCK_MODEL_ID),
  sheetsCredentialPresent:Boolean(env.GOOGLE_SERVICE_ACCOUNT_JSON_BASE64||env.GOOGLE_SERVICE_ACCOUNT_JSON||env.GOOGLE_APPLICATION_CREDENTIALS),
  sheetsIdPresent:Boolean(env.HOUSING_SHEET_ID||env.SHEET_ID),
  whapiTokenPresent:Boolean(env.WHAPI_API_TOKEN),
  whapiApiEnabled:env.EFPS_WHAPI_API_ENABLED==='true',
  whapiCatalogWriteEnabled:env.EFPS_WHAPI_CATALOG_WRITE_ENABLED==='true',
  whapiWebhookEnabled:env.EFPS_WHAPI_WEBHOOK_ENABLED!=='false',
  sourceAuditMcpEnabled:env.CRM_SOURCE_AUDIT_MCP_ENABLED==='true',
  sourceAuditTokenPresent:Boolean(env.CRM_SOURCE_AUDIT_TOKEN),
  liveDataEnabled:env.CRM_REAL_DATA_ENABLED==='true'
 };
}
function databaseFailure(error){
 const code=error?.code||error?.cause?.code;
 const name=error?.name||error?.cause?.name;
 const message=typeof error?.message==='string'?error.message:'';
 const category=code==='ENETUNREACH'||code==='EHOSTUNREACH'?'network':
  code==='ENOTFOUND'||code==='EAI_AGAIN'?'dns':
  code==='ETIMEDOUT'||code==='ESOCKET'?'timeout':
  code==='ECONNREFUSED'?'refused':
  code==='ECONNRESET'?'reset':
  code==='28P01'?'authentication':
  code==='3D000'?'database':
  code==='42501'?'permission':
  ['ERR_TLS_CERT_ALTNAME_INVALID','SELF_SIGNED_CERT_IN_CHAIN','UNABLE_TO_VERIFY_LEAF_SIGNATURE','DEPTH_ZERO_SELF_SIGNED_CERT'].includes(code)||/certificate|TLS|SSL/i.test(message)?'tls':'unknown';
 return {category,code:code?String(code):null,errorName:name?String(name):null};
}
export async function startupDatabaseCheck(env,{createRepository=createCrmRepository,log=console.info}={}){
 const flags=configurationStatus(env);
 // Never log the connection string, credentials, or raw exception.
 log('CRM configuration flags:',JSON.stringify(flags));
 log('CRM database endpoint shape:',JSON.stringify(connectionStringShape(env.DATABASE_URL,{sslCaConfigured:Boolean(env.DATABASE_SSL_CA)})));
 log('CRM database endpoint class:',connectionEndpointClass(env.DATABASE_URL));
 if(!flags.databaseUrlPresent){log('CRM database connectivity: not configured');return 'not_configured';}
 let repo;
 try{
  repo=createRepository({connectionString:env.DATABASE_URL,sslCa:env.DATABASE_SSL_CA});
  const ok=await repo.health();
  log('CRM database connectivity:',ok?'connected':'failed');
  return ok?'connected':'failed';
 }catch(error){
  const diagnostic=databaseFailure(error);
  log('CRM database connectivity: failed (category: '+diagnostic.category+')');
  log('CRM database connectivity diagnostic:',JSON.stringify(diagnostic));
  return 'failed';
 }finally{if(repo)try{await repo.close()}catch{}}
}
