import {createPublicKey,verify as verifySignature} from 'node:crypto';
import {repairCatalogCollections} from '../src/crm-source-audit.mjs';

const OIDC_ISSUER='https://token.actions.githubusercontent.com';
const OIDC_AUDIENCE='efps-crm-catalog-admin';
const OIDC_JWKS_URL=OIDC_ISSUER+'/.well-known/jwks';
const OIDC_REPOSITORY='zeidhussain9-cloud/efps-internal-automatios';
const OIDC_REF='refs/heads/main';
const OIDC_WORKFLOW_REF=OIDC_REPOSITORY+'/.github/workflows/crm-catalog-repair.yml@'+OIDC_REF;
let jwksCache=null;

function decode(value){return JSON.parse(Buffer.from(value,'base64url').toString('utf8'));}

async function authorized(req){
  const raw=String(req.headers.authorization||'').replace(/^Bearer\s+/i,'').trim();
  if(!raw||raw.split('.').length!==3)return false;
  try{
    const [h,p,s]=raw.split('.');
    const header=decode(h),claims=decode(p);
    if(header.alg!=='RS256'||!header.kid)return false;
    const audienceOk=claims.aud===OIDC_AUDIENCE||(Array.isArray(claims.aud)&&claims.aud.includes(OIDC_AUDIENCE));
    if(claims.iss!==OIDC_ISSUER||!audienceOk||claims.repository!==OIDC_REPOSITORY||claims.ref!==OIDC_REF||claims.sub!==`repo:${OIDC_REPOSITORY}:ref:${OIDC_REF}`)return false;
    if(claims.workflow_ref!==OIDC_WORKFLOW_REF&&claims.job_workflow_ref!==OIDC_WORKFLOW_REF)return false;
    const now=Math.floor(Date.now()/1000);
    if(!Number.isInteger(claims.exp)||claims.exp<now-30)return false;
    if(!jwksCache||jwksCache.expiresAt<now){
      const response=await fetch(OIDC_JWKS_URL);
      if(!response.ok)throw Error('OIDC JWKS unavailable');
      jwksCache={keys:(await response.json()).keys,expiresAt:now+300};
    }
    const jwk=jwksCache.keys.find(key=>key.kid===header.kid&&key.kty==='RSA');
    if(!jwk)return false;
    const key=createPublicKey({key:jwk,format:'jwk'});
    return verifySignature('RSA-SHA256',Buffer.from(h+'.'+p),key,Buffer.from(s,'base64url'));
  }catch{return false}
}

async function readBody(req){let raw='';for await(const chunk of req){raw+=chunk;if(raw.length>8192)throw Error('body too large')}return raw?JSON.parse(raw):{};}

export async function handleCatalogRepair(req,res){
  if(req.method!=='POST'||!(await authorized(req))){res.writeHead(401,{'Content-Type':'application/json','Cache-Control':'no-store'});return res.end(JSON.stringify({error:'catalog repair authentication required'}));}
  try{
    const body=await readBody(req);
    if(body.confirm!=='RECONCILE_56_59_63_64'){res.writeHead(400,{'Content-Type':'application/json','Cache-Control':'no-store'});return res.end(JSON.stringify({error:'explicit confirmation required'}));}
    const result=await repairCatalogCollections({dryRun:body.dry_run!==false});
    res.writeHead(result.ok?200:409,{'Content-Type':'application/json','Cache-Control':'no-store'});
    return res.end(JSON.stringify(result));
  }catch(error){
    console.error('Catalog repair failed',error?.message||error);
    res.writeHead(500,{'Content-Type':'application/json','Cache-Control':'no-store'});
    return res.end(JSON.stringify({ok:false,error:'catalog repair failed'}));
  }
}
