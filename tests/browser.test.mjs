import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {chromium} from 'playwright';
import {imageUrls} from '../src/crm-logic.mjs';
import {buildInventoryPage,INVENTORY_PAGE_SIZE} from '../src/inventory-logic.mjs';

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
    leads:[
     {id:'LIVE-1',display_name:'Live lead',normalized_phone:'+919000000001',status:'New',lead_type:'New',tenant_type:'Not specified',priority:'Medium',classification:'Qualified Lead',auto_qualified:true,overdue_followup_count:1,requirements:{bhk:'2 BHK',locality:'Harlur',budget:50000},updated_at:'2026-09-30T00:00:00Z',contacted_at:'2026-08-26T07:30:00.000Z',last_message_direction:'Incoming',last_message_at:'2026-09-30T16:26:15.000Z',source_number:'+919148338801'},
     {id:'LIVE-2',display_name:'Unclassified lead',normalized_phone:'+919000000002',status:'New',lead_type:'Waiting on Customer',tenant_type:'Not specified',priority:'Medium',classification:'Cold Inquiry',overdue_followup_count:0,requirements:{},updated_at:'2026-09-30T00:00:00Z',contacted_at:null,last_message_direction:null,last_message_at:null,source_number:'+919148338801'}
    ],
   total:228,sourceTotals:{'+919148338801':228}
  })}));

  await page.route('**/api/db/stats*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({
   sourceNumber:'+919148338801',leadCount:228,liveLeadCount:3,pendingClassificationCount:4,notPushedClassificationCount:4,qualifiedClassificationCount:228,availableInventoryCount:2,webhookErrorCount:0,leadStatusCounts:[{status:'New',count:12},{status:'Active Follow-up',count:40},{status:'Waiting on Customer',count:18},{status:'Waiting on Us',count:10},{status:'Nurture',count:30},{status:'Dormant',count:25},{status:'Converted',count:8},{status:'Lost',count:15},{status:'On Hold',count:20},{status:'Out of Coverage Area',count:50}],followupTotal:12,followupHasMore:true,nextFollowups:Array.from({length:10},(_,i)=>({id:i+1,lead_id:'LIVE-1',due_at:`2026-10-02T0${i}:00:00Z`,note:`Follow-up ${i+1}`,display_name:`Live lead ${i+1}`,normalized_phone:'+919000000001'})),supportedSourceNumbers:['+919148338801','+917975102130','+919902024973']
  })}));

  await page.route('https://res.cloudinary.com/**',route=>route.fulfill({status:200,contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="320" height="220"><rect width="320" height="220" fill="#dce8f0"/></svg>'}));
  const inventoryRows=[
    {listing_id:'INV-3',locality:'Sarjapur',society_name:'Society 3',bhk:'3 BHK',monthly_rent:70000,furnishing:'Fully Furnished',listing_state:'Available',pet_friendly:'No',cloudinary_image_urls:['https://res.cloudinary.com/test/properties/INV-3/photo_1.jpg'],source_record:{onboarded_on:'30 Sep 2026, 8:00 AM',city:'Bengaluru'},last_synced_at:'2026-10-01T12:45:01Z'},
    {listing_id:'INV-1',locality:'Bellandur',society_name:'Society 1',bhk:'1 BHK',monthly_rent:22000,furnishing:'Semi Furnished',listing_state:'Rented Out',pet_friendly:'Yes',cloudinary_image_urls:[],source_record:{onboarded_on:'25 Sep 2026, 8:00 AM',city:'Bengaluru'},last_synced_at:'2026-10-01T12:45:01Z'},
    {listing_id:'INV-2',locality:'Harlur',society_name:'Society 2',bhk:'2 BHK',monthly_rent:45000,furnishing:'Unfurnished',listing_state:'Available',pet_friendly:'Unknown',cloudinary_image_urls:['https://res.cloudinary.com/test/properties/INV-2/photo_1.jpg'],source_record:{onboarded_on:'28 Sep 2026, 8:00 AM',city:'Bengaluru'},last_synced_at:'2026-10-01T12:45:01Z'},
    ...Array.from({length:24},(_,index)=>{const id=String(index+4).padStart(2,'0');return{listing_id:'INV-'+id,locality:'Harlur',society_name:'Society '+id,bhk:'2 BHK',monthly_rent:85000+index,furnishing:'Not specified',listing_state:'Rented Out',pet_friendly:'Unknown',cloudinary_image_urls:[],source_record:{onboarded_on:'01 Oct 2026, 8:00 AM',city:'Bengaluru'},last_synced_at:'2026-10-01T12:45:01Z'}})
   ];
  await page.route('**/api/inventory/overview*',async route=>{
   const params=new URL(route.request().url()).searchParams;
   const withPhotos=params.get('with_photos');
   const data=buildInventoryPage(inventoryRows,{limit:Number(params.get('limit')||INVENTORY_PAGE_SIZE),offset:Number(params.get('offset')||0),sort:params.get('inventory_sort')||'latest',status:params.get('status')||'All',bhk:params.get('bhk')||'All',locality:params.get('locality')||'All',withPhotos:withPhotos===''||withPhotos===null?null:withPhotos==='true',search:params.get('search')||''},row=>imageUrls(row).length>0);
   await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({...data,sort:params.get('inventory_sort')||'latest',latestSync:{created_at:'2026-10-01T12:45:01Z',row_count:88,changed_count:0,removed_count:0}})});
  });

  await page.route('**/api/db/leads/*/workspace*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({
   lead:{id:'LIVE-1',display_name:'Live lead',normalized_phone:'+919000000001',status:'New',lead_type:'New',tenant_type:'Not specified',priority:'Medium',classification:'Qualified Lead',requirements:{bhk:'2 BHK',locality:'Harlur',budget:50000},operator_notes:''},
   sources:[{source_number:'+919148338801'}],
   messages:[{id:1,source_number:'+919148338801',source_message_id:'MSG-1',direction:'Incoming',message_type:'text',body:'Property: https://housing.com/rent/12345-2-bhk-harlur',sender_name:'Customer',message_at:'2026-09-30T00:00:00Z'},{id:2,source_number:'+919148338801',source_message_id:'MSG-2',replied_to_source_message_id:'MSG-1',direction:'Outgoing',message_type:'text',body:'Historical conversation message',sender_name:'EasyFind',message_at:'2026-09-30T00:01:00Z'},{id:3,source_number:'+919148338801',direction:'Incoming',message_type:'text',body:'General requirement discussion',sender_name:'Customer',message_at:'2026-09-30T00:02:00Z'}],
   requirement_profile:{bhk:'2 BHK',budget:'50000',preferred_locations:'Harlur',tenant_type:'Family',furnishing:'Any',parking:'Any',pets:'Unknown',preferred_amenities:[],notes:''},
   activity:[],followups:[],drafts:[{id:'DRAFT-2',version:2,body:'Hello from persisted draft',status:'draft',created_at:'2026-10-01T02:30:00Z',ai_run_id:'RUN-2',ai_provider:'aws-bedrock',model_name:'au.anthropic.claude-opus-4-6-v1',input_tokens:12000,output_tokens:850,total_tokens:12850,estimated_cost_usd:0.08125},{id:'DRAFT-1',version:1,body:'Older draft',status:'draft',created_at:'2026-10-01T02:29:00Z',ai_run_id:'RUN-1',ai_provider:'ollama',model_name:'gpt-oss:20b'}],ai_runs:[{id:'RUN-2',model_name:'au.anthropic.claude-opus-4-6-v1',status:'proposed',created_at:'2026-10-01T02:30:00Z',input_tokens:12000,output_tokens:850,total_tokens:12850,estimated_cost_usd:0.08125}]
  })}));

  await page.route('**/api/db/leads/LIVE-1',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({id:'LIVE-1',lead_type:'Active Follow-up',tenant_type:'Family'})}));
  await page.route('**/api/inventory/matches*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({rows:[]})}));
  await page.route('**/api/audit/recent*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({rows:[{id:900,action:'lead.updated',actor:'pilot',lead_id:'LIVE-1',occurred_at:'2026-10-01T10:00:00Z',details:{field:'status'}}],hasMore:false})}));
  await page.route('**/api/audit/lead/*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({rows:[{id:901,action:'requirements.updated',actor:'pilot',lead_id:'LIVE-1',occurred_at:'2026-10-01T10:01:00Z',details:{fields:['bhk']}}],hasMore:false})}));

  await page.goto(base);
  await page.getByRole('heading',{name:'Operator sign in'}).waitFor();
  await page.getByLabel('Username').fill('pilot');
  await page.getByLabel('Password').fill('test-pass');
  await page.getByRole('button',{name:'Sign in'}).click();

  await page.getByText('Production data').waitFor();
  await page.getByText('228',{exact:true}).first().waitFor();
  await page.getByText('Actually qualified',{exact:false}).waitFor();
  await page.getByText('Waiting for classification',{exact:false}).waitFor();
  await page.getByText('Total available inventory',{exact:false}).waitFor();
  await page.getByText('Follow-ups',{exact:true}).first().waitFor();

  await page.getByRole('button',{name:'Inventory',exact:true}).click();
  assert.equal(new URL(page.url()).pathname,'/inventory');
  await page.getByRole('heading',{name:'Property inventory'}).waitFor();
  await page.getByRole('button',{name:/Total properties/}).waitFor();
  assert.equal(await page.getByRole('button',{name:/Total properties/}).count(),1);
  assert.equal(await page.getByRole('button',{name:/Available/}).count(),1);
  assert.equal(await page.getByRole('button',{name:/Rented out/}).count(),1);
  assert.equal(await page.getByRole('button',{name:/With photos/}).count(),1);
  await page.getByRole('button',{name:/Available/}).click();
  await page.getByText('2 properties',{exact:true}).waitFor();
  assert.equal(await page.locator('.inventory-card').count(),2);
  assert.equal(await page.getByLabel('Inventory per page').inputValue(),'10');
  await page.getByRole('button',{name:/With photos/}).click();
  await page.getByText('2 properties',{exact:true}).waitFor();
  assert.equal(await page.locator('.inventory-card').count(),2);
  assert.equal(await page.locator('.inventory-card img').count(),2);
  await page.getByRole('button',{name:'Total properties'}).click();
  const oldestRequest=page.waitForRequest(request=>{
   try{return request.url().includes('/api/inventory/overview')&&new URL(request.url()).searchParams.get('inventory_sort')==='oldest'}catch{return false}
  });
  await page.getByLabel('Sort inventory').selectOption('oldest');
  await oldestRequest;
  await page.locator('.inventory-card').first().getByText(/INV-1/).waitFor();
  await page.getByRole('button',{name:'Total properties'}).click();
  await page.getByRole('button',{name:/View property/}).first().click();
  await page.getByRole('dialog',{name:'Property details'}).waitFor();
  await page.getByRole('button',{name:/Close/}).click();
  await page.getByLabel('Inventory per page').selectOption('20');
  const nextInventoryResponse=page.waitForResponse(response=>{try{const params=new URL(response.url()).searchParams;return response.url().includes('/api/inventory/overview')&&params.get('offset')==='20'&&params.get('limit')==='20'&&response.status()===200}catch{return false}});
  await page.getByRole('button',{name:'Next inventory page'}).click();
  await nextInventoryResponse;
  await page.getByText('Page 2 · 21–27 of 27',{exact:true}).waitFor();
  assert.equal(await page.locator('.inventory-card').count(),7);
  const resetInventoryRequest=page.waitForRequest(request=>{
   try{const params=new URL(request.url()).searchParams;return request.url().includes('/api/inventory/overview')&&params.get('status')==='Available'&&params.get('offset')==='0'}catch{return false}
  });
  await page.getByRole('button',{name:/Available/}).click();
  await resetInventoryRequest;
  await page.getByText('2 properties',{exact:true}).waitFor();

  await page.getByRole('button',{name:'Leads Inbox',exact:true}).click();
  assert.equal(new URL(page.url()).pathname,'/leads');
  await page.getByLabel('Sort leads').waitFor();
  const activeFollowupSummary=page.getByRole('button',{name:/^Active Follow-up.*40/});
  await activeFollowupSummary.waitFor();
  assert.equal(await page.locator('.lead-card-activity').count(),2);
  assert.equal(await page.getByText('Classification',{exact:true}).count(),0);
  assert.equal(await page.getByText('Qualified Lead',{exact:true}).count(),0);
  assert.equal(await page.getByText('AUTO QUALIFIED',{exact:true}).count(),1);
  assert.equal(await page.locator('.lead-card-status-panel').count(),2);
  assert.equal(await page.locator('.lead-card-status-panel strong').nth(0).textContent(),'New');
  assert.equal(await page.locator('.lead-card-status-panel strong').nth(1).textContent(),'Waiting on Customer');
  assert.equal(await page.locator('.lead-card-status-panel').filter({hasText:'New'}).count(),1);
  assert.equal(await page.locator('.lead-card-status-panel').filter({hasText:'Waiting on Customer'}).count(),1);
  assert.equal(await page.getByText('Source number · +919148338801',{exact:true}).count(),2);
  assert.equal(await page.getByText('Overdue follow-up · 1',{exact:true}).count(),1);
  assert.equal(await page.getByText(/financial risk|budget risk/i).count(),0,'no inferred financial-risk cue is shown');
  assert.equal(await page.getByText('Contacted date',{exact:true}).count(),2);
  assert.equal(await page.getByText('Last message sent by',{exact:true}).count(),2);
  assert.equal(await page.getByText('Last message date',{exact:true}).count(),2);
  assert.equal(await page.getByLabel('Leads per page').inputValue(),'10');
  const leadPageSizeRequest=page.waitForRequest(request=>{try{return request.url().includes('/api/db/leads')&&new URL(request.url()).searchParams.get('limit')==='20'}catch{return false}});
  await page.getByLabel('Leads per page').selectOption('20');
  await leadPageSizeRequest;
  assert.equal(await activeFollowupSummary.locator('b').textContent(),'40');
  await activeFollowupSummary.click();
  await page.locator('.lead-card-status-panel').filter({hasText:'New'}).waitFor();

  const sortRequest=page.waitForRequest(request=>{
   try{return request.url().includes('/api/db/leads')&&new URL(request.url()).searchParams.get('lead_sort')==='customer_waiting'}catch{return false}
  });
  await page.getByLabel('Sort leads').selectOption('customer_waiting');
  await sortRequest;

  const searchRequest=page.waitForRequest(request=>{
   try{return request.url().includes('/api/db/leads')&&new URL(request.url()).searchParams.get('lead_search')==='live'}catch{return false}
  });
  await page.getByLabel('Search live leads').fill('live');
  await searchRequest;

  const phoneText=await page.locator('.lead-card-main span').first().textContent();
  assert.match(phoneText||'',/\*\*\*\*\*\*0001$/);
  assert.equal(await page.getByText('Synthetic preview').count(),0);
  assert.equal(await page.getByText('Sample leads').count(),0);

  const leadButton=page.getByRole('button',{name:/Live lead/}).first();
  await leadButton.waitFor();
  const workspaceResponsePromise=page.waitForResponse(response=>response.url().includes('/api/db/leads/LIVE-1/workspace'));
  await leadButton.click();
  assert.equal(new URL(page.url()).pathname,'/leads/LIVE-1/overview');
  const workspaceResponse=await workspaceResponsePromise;
  assert.equal(workspaceResponse.status(),200);
  console.log('LEAD_WORKSPACE_BODY_AFTER_RESPONSE:',await page.locator('body').innerText());
  console.log('LEAD_DETAIL_COUNT:',await page.locator('.live-detail').count());
  console.log('OVERVIEW_TAB_COUNT:',await page.getByRole('tab',{name:'Overview',exact:true}).count());

  await page.getByRole('tab',{name:'Overview',exact:true}).waitFor();
  await page.getByRole('heading',{name:'Live lead',exact:true}).waitFor();
  assert.equal(await page.getByText('Actual lead',{exact:true}).count(),0);
  assert.equal(await page.getByText(/Priority · Medium/,{exact:true}).count(),0);
  await page.getByLabel('Lead Status').waitFor();
  const oocOption=page.getByLabel('Lead Status').locator('option[value="Out of Coverage Area"]');
  assert.equal(await oocOption.count(),1);
  assert.equal(await oocOption.textContent(),'OOC');
  await page.getByLabel('Tenant Type').waitFor();

  await page.getByRole('tab',{name:'Conversation',exact:true}).click();
  assert.equal(new URL(page.url()).pathname,'/leads/LIVE-1/conversation');
  await page.getByText('Sensitive message hidden').first().waitFor();
  await page.getByRole('button',{name:/Privacy: Masked/}).click();
  await page.getByText('Property reference',{exact:true}).waitFor();
  await page.getByText('Messages without an explicit property reference',{exact:true}).waitFor();
  await page.getByText('Historical conversation message').waitFor();

  await page.getByRole('tab',{name:'Requirements',exact:true}).click();
  assert.equal(new URL(page.url()).pathname,'/leads/LIVE-1/requirements');
  await page.getByText('Editable normalized requirement profile.',{exact:false}).waitFor();
  assert.equal(await page.locator('.requirements-table').count(),1);
  assert.equal(await page.getByLabel('Requirements per page').inputValue(),'10');
  assert.equal(await page.locator('.requirements-table tbody tr').count(),10);
  await page.getByRole('button',{name:'Next',exact:true}).last().click();
  assert.equal(await page.locator('.requirements-table tbody tr').count(),6);

  await page.getByRole('tab',{name:'Activity & History',exact:true}).click();
  assert.equal(new URL(page.url()).pathname,'/leads/LIVE-1/activity-history');
  await page.getByText('Lead audit history',{exact:true}).waitFor();
  assert.equal(await page.getByLabel('Lead audit date range').count(),1);
  assert.deepEqual(await page.getByLabel('Lead audit date range').locator('option').allTextContents(),['All activity','Today','Last 7 days','Last 30 days','This month','Previous month','Custom range']);
  await page.getByText('requirements.updated',{exact:true}).waitFor();

  await page.getByRole('tab',{name:'Property Matches',exact:true}).click();
  assert.equal(new URL(page.url()).pathname,'/leads/LIVE-1/property-matches');
  await page.getByText(/No live inventory matches were returned/).waitFor();

  await page.getByRole('tab',{name:'AI & Drafts',exact:true}).click();
  assert.equal(new URL(page.url()).pathname,'/leads/LIVE-1/ai-drafts');
  await page.getByText(/Production AI reviews the complete chronological conversation/).waitFor();
  await page.getByRole('button',{name:'Open draft version 2'}).waitFor();
  await page.getByRole('button',{name:'Open draft version 2'}).click();
  const persistedDraft=page.locator('textarea.draft-editor');
  await persistedDraft.waitFor();
  assert.equal(await persistedDraft.inputValue(),'Hello from persisted draft');
  assert.equal(await page.getByText(/au\.anthropic\.claude-opus-4-6-v1 · aws-bedrock/).count(),2);
  await page.getByText('Input tokens: 12,000',{exact:true}).waitFor();
  await page.getByText('Output tokens: 850',{exact:true}).waitFor();
  await page.getByText('Estimated cost: $0.081250',{exact:true}).waitFor();

  await page.getByRole('button',{name:'Dashboard',exact:true}).click();
  assert.equal(new URL(page.url()).pathname,'/dashboard');
  await page.getByRole('button',{name:'Activity',exact:true}).click();
  assert.equal(new URL(page.url()).pathname,'/activity');
  await page.getByText('All CRM activity across leads',{exact:false}).waitFor();
  assert.equal(await page.getByLabel('Audit date range').count(),1);
  assert.deepEqual(await page.getByLabel('Audit date range').locator('option').allTextContents(),['All activity','Today','Last 7 days','Last 30 days','This month','Previous month','Custom range']);
  await page.getByText('lead.updated',{exact:true}).waitFor();
  await page.getByText('Lead',{exact:true}).last().waitFor();


  // Exercise the compact/tablet viewport used by mobile browsers that expose a wider layout viewport.
  await page.getByRole('button',{name:'Dashboard',exact:true}).click();
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

  await page.setViewportSize({width:390,height:844});
  await page.reload();
  await page.getByText('Production data').waitFor();
  const toolbarBox=await page.locator('.production-toolbar').boundingBox();
  assert.ok(toolbarBox&&toolbarBox.width<=390,'lead controls fit the mobile viewport');
  const sortBox=await page.getByLabel('Sort leads').boundingBox();
  assert.ok(sortBox&&sortBox.width>0&&sortBox.width<=195,'sort control stays within its mobile column');
  const activity=await page.locator('.lead-card-activity').first().boundingBox();
  assert.ok(activity&&activity.width<=390,'lead activity columns fit the mobile card');
  assert.equal(await page.getByLabel('Sort leads').locator('option').count(),5,'all lead sort modes remain available on mobile');
  await page.getByRole('button',{name:'Leads Inbox',exact:true}).click();
  await page.locator('.lead-card-status-panel').first().waitFor();
  const identityBox=await page.locator('.lead-card-identity').first().boundingBox();
  const statusBox=await page.locator('.lead-card-status-panel').first().boundingBox();
  assert.ok(identityBox&&statusBox&&statusBox.y>=identityBox.y+identityBox.height+6,'lead status remains separated from lead identity on mobile');
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth),'lead cards do not create horizontal page overflow at 390px');

 }finally{await browser?.close();server.kill()}
});
