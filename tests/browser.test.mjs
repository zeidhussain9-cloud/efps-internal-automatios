import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {chromium} from 'playwright';

const port=18763,base='http://127.0.0.1:'+port;
const startServer=()=>spawn(process.execPath,['crm-server.mjs'],{
 env:{...process.env,PORT:String(port),CRM_BASIC_AUTH_USERNAME:'',CRM_BASIC_AUTH_PASSWORD:''},
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
  await page.route('**/api/db/leads/*/workspace',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({
   lead:{id:'LIVE-1',display_name:'Live lead',normalized_phone:'+919000000001',status:'New',lead_type:'New',tenant_type:'Not specified',priority:'Medium',classification:'Qualified Lead',requirements:{bhk:'2 BHK',locality:'Harlur',budget:50000},operator_notes:''},
   sources:[{source_number:'+919148338801'}],messages:[{id:1,source_number:'+919148338801',direction:'Incoming',message_type:'text',body:'Historical conversation message',sender_name:'Customer',message_at:'2026-09-30T00:00:00Z'}],activity:[],followups:[]
  })}));
  await page.route('**/api/db/leads/LIVE-1',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({id:'LIVE-1',lead_type:'Active Follow-up',tenant_type:'Family'})}));
  await page.route('**/api/inventory/matches?*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({rows:[]})}));
  await page.goto(base);
  assert.equal(await page.getByText('Production data').count(),1);
  assert.equal(await page.getByText('Synthetic preview').count(),0);
  assert.equal(await page.getByText('Sample leads').count(),0);
  assert.equal(await page.getByText('Live lead').count(),1);
  assert.equal(await page.getByText('Actual lead').count(),1);
  await page.getByText('228 leads').waitFor();
  assert.equal(await page.getByText('228 leads').count(),1);
  await page.getByRole('button',{name:/Live lead/}).click();
  await page.getByRole('button',{name:'Overview',exact:true}).waitFor();
  assert.equal(await page.getByText('Live lead').count()>0,true);
  assert.equal(await page.getByText('Lead Status').count(),1);
  assert.equal(await page.getByText('Tenant Type').count(),1);
  await page.getByLabel('Lead Status').selectOption('Active Follow-up');
  await page.getByLabel('Tenant Type').selectOption('Family');
  assert.equal(await page.getByText('No imported conversation for this lead.').count(),0);
  await page.getByRole('button',{name:'Conversation',exact:true}).click();
  assert.equal(await page.getByText('Historical conversation message').count(),1);
  await page.locator('button.header-back').click();
  await page.getByText('228 leads').waitFor();
  assert.equal(await page.getByText('228 leads').count(),1);
  await page.getByRole('button',{name:/Live lead/}).click();
  await page.getByRole('button',{name:'Property Matches',exact:true}).click();
  assert.equal(await page.getByText(/No live inventory matches were returned/).count(),1);
  await page.getByRole('button',{name:'AI & Drafts',exact:true}).click();
  assert.equal(await page.getByText(/Real AI is on-demand/).count(),1);
  await page.locator('button.header-back').click();
  assert.equal(await page.getByText('Production data').count(),1);
 }finally{await browser?.close();server.kill()}
});
