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

  await page.route('**/api/db/leads*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({
   leads:[{id:'LIVE-1',display_name:'Live lead',normalized_phone:'+919000000001',status:'New',lead_type:'New',tenant_type:'Not specified',priority:'Medium',classification:'Qualified Lead',requirements:{bhk:'2 BHK',locality:'Harlur',budget:50000},updated_at:'2026-09-30T00:00:00Z',source_number:'+919148338801'}],
   total:228,sourceTotals:{'+919148338801':228}
  })}));

  await page.route('**/api/db/stats*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({
   sourceNumber:'+919148338801',leadCount:228,liveLeadCount:3,pendingClassificationCount:4,webhookErrorCount:0,supportedSourceNumbers:['+919148338801','+917975102130','+919902024973']
  })}));

  await page.route('**/api/inventory/overview*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({rows:[],latestSync:null})}));

  await page.route('**/api/db/leads/*/workspace*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({
   lead:{id:'LIVE-1',display_name:'Live lead',normalized_phone:'+919000000001',status:'New',lead_type:'New',tenant_type:'Not specified',priority:'Medium',classification:'Qualified Lead',requirements:{bhk:'2 BHK',locality:'Harlur',budget:50000},operator_notes:''},
   sources:[{source_number:'+919148338801'}],
   messages:[{id:1,source_number:'+919148338801',direction:'Incoming',message_type:'text',body:'Historical conversation message',sender_name:'Customer',message_at:'2026-09-30T00:00:00Z'}],
   activity:[],followups:[]
  })}));

  await page.route('**/api/db/leads/LIVE-1',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({id:'LIVE-1',lead_type:'Active Follow-up',tenant_type:'Family'})}));
  await page.route('**/api/inventory/matches*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({rows:[]})}));

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

  const leadButton=page.getByRole('button',{name:/Live lead/}).first();
  await leadButton.waitFor();
  await leadButton.click();

  await page.getByRole('button',{name:'Overview',exact:true}).waitFor();
  await page.getByRole('heading',{name:'Live lead',exact:true}).waitFor();
  await page.getByLabel('Lead Status').waitFor();
  await page.getByLabel('Tenant Type').waitFor();

  await page.getByRole('button',{name:'Conversation',exact:true}).click();
  await page.getByText('Sensitive message hidden').waitFor();
  await page.getByRole('button',{name:/Privacy: Masked/}).click();
  await page.getByText('Historical conversation message').waitFor();

  await page.getByRole('button',{name:'Property Matches',exact:true}).click();
  await page.getByText(/No live inventory matches were returned/).waitFor();

  await page.getByRole('button',{name:'AI & Drafts',exact:true}).click();
  await page.getByText(/Real AI is on-demand/).waitFor();

  await page.locator('button.header-back').click();
  await page.getByText('Production data').waitFor();

  // Exercise the compact/tablet viewport used by mobile browsers that expose a wider layout viewport.
  await page.setViewportSize({width:900,height:800});
  await page.reload();
  await page.getByText('Production data').waitFor();
  const sidebarBox=await page.locator('.sidebar').boundingBox();
  const mainBox=await page.locator('.main').boundingBox();
  assert.ok(sidebarBox&&sidebarBox.width>=899,'compact viewport uses full-width navigation');
  assert.ok(mainBox&&mainBox.width>=899,'compact viewport keeps the CRM content full-width');
  const statBoxes=await page.locator('.stats .stat').evaluateAll(nodes=>nodes.slice(0,2).map(n=>{const r=n.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width}}));
  assert.equal(statBoxes.length,2);
  assert.ok(Math.abs(statBoxes[0].y-statBoxes[1].y)<2,'dashboard KPI cards remain in a two-column mobile layout');

 }finally{await browser?.close();server.kill()}
});
