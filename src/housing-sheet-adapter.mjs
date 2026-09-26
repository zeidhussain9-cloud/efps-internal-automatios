// Read-only Housing Listings adapter. Never creates, edits or deletes sheet rows.
import {createSign} from 'node:crypto';
const base64url=value=>Buffer.from(typeof value==='string'?value:JSON.stringify(value)).toString('base64url');
export function sheetSettings(env){return{ready:Boolean((env.GOOGLE_SERVICE_ACCOUNT_JSON_BASE64||env.GOOGLE_APPLICATION_CREDENTIALS)&&(env.HOUSING_SHEET_ID||env.SHEET_ID)&&env.HOUSING_SHEET_TAB),sheetId:env.HOUSING_SHEET_ID||env.SHEET_ID||null,tab:env.HOUSING_SHEET_TAB||null};}
export function decodeServiceAccount(encoded){let json;try{json=JSON.parse(encoded.trim().startsWith('{')?encoded:Buffer.from(encoded,'base64').toString('utf8'))}catch{throw Error('Invalid service-account JSON encoding')}if(json?.type!=='service_account'||!json.client_email||!json.private_key||!json.token_uri?.startsWith('https://oauth2.googleapis.com/'))throw Error('Invalid service-account JSON fields');return json;}
export async function readHousingSheet({env,fetcher=fetch}){
 if(env.CRM_SYNTHETIC_SHEETS_ENABLED!=='true')throw Error('Sheets adapter disabled');
 const settings=sheetSettings(env);if(!settings.ready)throw Error('Sheet configuration incomplete');
 const account=decodeServiceAccount(env.GOOGLE_SERVICE_ACCOUNT_JSON_BASE64||env.GOOGLE_APPLICATION_CREDENTIALS);
 const now=Math.floor(Date.now()/1000),header=base64url({alg:'RS256',typ:'JWT'}),claims=base64url({iss:account.client_email,scope:'https://www.googleapis.com/auth/spreadsheets.readonly',aud:account.token_uri,iat:now,exp:now+3000});const input=header+'.'+claims;const signer=createSign('RSA-SHA256');signer.update(input);const jwt=input+'.'+signer.sign(account.private_key).toString('base64url');
 const tokenResponse=await fetcher(account.token_uri,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams({grant_type:'urn:ietf:params:oauth:grant-type:jwt-bearer',assertion:jwt})});if(!tokenResponse.ok)throw Error('Sheets token request failed ('+tokenResponse.status+')');const token=await tokenResponse.json();if(!token.access_token)throw Error('Sheets token missing');
 const range=encodeURIComponent("'"+settings.tab.replaceAll("'","''")+"'!A:AV");const url='https://sheets.googleapis.com/v4/spreadsheets/'+encodeURIComponent(settings.sheetId)+'/values/'+range;
 const response=await fetcher(url,{method:'GET',headers:{Authorization:'Bearer '+token.access_token}});if(!response.ok)throw Error('Read-only Sheets request failed ('+response.status+')');const result=await response.json();return{range:result.range||null,rows:Array.isArray(result.values)?result.values:[],readOnly:true};
}
