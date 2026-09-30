import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {chromium} from 'playwright';

const port=18763,base='http://127.0.0.1:'+port;
const startServer=()=>spawn(process.execPath,['crm-server.mjs'],{
 env:{...process.env,PORT:String(port),CRM_BASIC_AUTH_USERNAME:'pilot',CRM_BASIC_AUTH_PASSWORD:'test-pass',CRM_DB_READ_ENABLED:'true',CRM_DB_WRITE_ENABLED:'true',DATABASE_URL:''},
 stdio:'pipe'
});
const waitForServer=async()=>{
 for(let i=0;i<50;i++){try{const r=await fetch(base+'/health');if(r.ok)return true}catch{}await new Promise(resolve=>setTimeout(resolve,200))}
 return false;
};

test('production CRM browser journey uses only live-record surfaces',async()=>{
 const server=startServer();let browser;
 try{
  assert.equal(await waitForServer(),true,'server starts');
  browser=await chromium.launch({headless:true});
  const page=await browser.newPage();
  await page.route('**/api/db/leads?*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({
   leads:[{id:'LIVE-1',display_name:'Live lead',normalized_phone:'+919000000001',status:'New',priority:'Medium',classification:'Qualified Lead',requirements:{bhk:'2 BHK',locality:'Harlur',budget:50000},updated_at:'2026-09-30T00:00:00Z',source_number:'+919148338801'}],
   total:228,sourceTotals:{'+919148338801':228}
  })}));
  await page.route('**/api/db/stats?*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({sourceNumber:'+919148338801',leadCount:228,liveLeadCount:3,pendingClassificationCount:4,webhookErrorCount:0,supportedSourceNumbers:['+919148338801','+917975102130','+919902024973']})}));
  await page.route('**/api/inventory/overview',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({rows:[],latestSync:null})}));
  let archived=false;
  await page.route('**/api/db/leads/*/workspace*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({
   lead:{id:'LIVE-1',display_name:'Live lead',normalized_phone:'+919000000001',status:archived?'Archived':'New',lead_type:'New',tenant_type:'Not specified',priority:'Medium',classification:'Qualified Lead',requirements:{bhk:'2 BHK',locality:'Harlur',budget:50000},operator_notes:''},
   sources:[{source_number:'+919148338801'}],messages:[{id:1,source_number:'+919148338801',direction:'Incoming',message_type:'text',body:'Historical conversation message',sender_name:'Customer',message_at:'2026-09-30T00:00:00Z'}],activity:[],followups:[]
  })}));
  await page.route('**/api/db/leads/LIVE-1',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({id:'LIVE-1',lead_type:'Active Follow-up',tenant_type:'Family'})}));
  await page.route('**/api/inventory/matches?*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({rows:[]})}));
  await page.route('**/api/audit/recent?*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({rows:[{id:1,action:'auth.login',actor:'pilot',occurred_at:'2026-09-30T00:00:00Z',details:{via:'password'}}]})}));
  await page.route('**/api/db/export?*',route=>route.fulfill({status:200,contentType:'text/csv',body:'id,display_name\nLIVE-1,Live lead\n'}));
  await page.route('**/api/db/leads/LIVE-1/archive',route=>{archived=true;return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({id:'LIVE-1',status:'Archived',lead_type:'New',tenant_type:'Not specified'})})});
  await page.route('**/api/db/leads/LIVE-1/restore',route=>{archived=false;return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({id:'LIVE-1',status:'New',lead_type:'New',tenant_type:'Not specified'})})});
  await page.goto(base);
  await page.getByRole('heading',{name:'Operator sign in'}).waitFor();
  await page.getByLabel('Username').fill('pilot');
  await page.getByLabel('Password').fill('test-pass');
  await page.getByRole('button',{name:'Sign in'}).click();
  await page.getByText('Production data').waitFor();
  await page.getByText('228 leads').waitFor();
  const phoneText=await page.locator('.lead-card-main span').first().textContent();
  assert.match(phoneText||'',/\*\*\*\*\*\*0001$/);
  assert.equal(await page.getByText('Synthetic preview').count(),0);
  assert.equal(await page.getByText('Sample leads').count(),0);
  assert.equal(await page.getByText('Live lead').count(),1);
  assert.equal(await page.getByText('Actual lead').count(),1);
  await page.getByRole('button',{name:/Live lead/}).waitFor();
  await page.getByRole('button',{name:/Live lead/}).click();
  await page.getByRole('button',{name:'Overview',exact:true}).waitFor();
  await page.getByRole('button',{name:/Privacy: Masked/}).click();
  await page.getByRole('button',{name:/Privacy: Revealed/}).waitFor();
  await page.getByRole('button',{name:/Privacy: Revealed/}).click();
  await page.getByRole('heading',{name:'Live lead',exact:true}).waitFor();
  await page.getByText('Lead Status').waitFor();
  await page.getByText('Tenant Type').waitFor();
  await page.getByLabel('Lead Status').selectOption('Active Follow-up');
  await page.context().setOffline(true);
  await page.getByText('Offline. Reading the current UI is allowed').waitFor();
  assert.equal(await page.getByLabel('Lead Status').isDisabled(),true);
  assert.equal(await page.getByRole('button',{name:'Archive lead'}).isDisabled(),true);
  await page.context().setOffline(false);
  await page.waitForFunction(()=>navigator.onLine===true);
  await page.getByText('Online',{exact:true}).waitFor();
  await page.getByLabel('Tenant Type').selectOption('Family');
  const archiveButton=page.getByRole('button',{name:'Archive lead'});
  await archiveButton.waitFor();
  await page.once('dialog',dialog=>dialog.accept());
  await archiveButton.click();
  await page.getByRole('button',{name:'Restore lead'}).waitFor();
  await page.getByRole('button',{name:'Restore lead'}).click();
  await page.getByRole('button',{name:'Archive lead'}).waitFor();
  await page.getByRole('button',{name:'Conversation',exact:true}).click();
  await page.getByText('Sensitive message hidden').waitFor();
  await page.getByRole('button',{name:/Privacy: Masked/}).click();
  await page.getByText('Historical conversation message').waitFor();
  await page.locator('button.header-back').click();
  await page.getByRole('button',{name:/Live lead/}).waitFor();
  await page.getByRole('button',{name:/Live lead/}).click();
  await page.getByRole('button',{name:'Overview',exact:true}).waitFor();
  await page.getByRole('button',{name:'Property Matches',exact:true}).click();
  await page.getByText(/No live inventory matches were returned/).waitFor();
  await page.getByRole('button',{name:'AI & Drafts',exact:true}).click();
  await page.getByText(/Real AI is on-demand/).waitFor();
  await page.locator('button.header-back').click();
  await page.getByText('Production data').waitFor();
  await page.getByRole('button',{name:'Activity',exact:true}).click();
  await page.getByText('Audit Activity').waitFor();
  await page.getByText('auth.login').waitFor();
  await page.getByRole('button',{name:'Settings',exact:true}).click();
  await page.getByText('Data controls').waitFor();
  await page.getByRole('button',{name:/Export \+919148338801/}).waitFor();
 }finally{await browser?.close();server.kill()}
});
