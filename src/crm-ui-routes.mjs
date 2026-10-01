export const CRM_PAGE_PATHS=Object.freeze({
 Dashboard:'/dashboard',
 'Contact Classification':'/classification',
 'Leads Inbox':'/leads',
 Inventory:'/inventory',
 Activity:'/activity',
 Settings:'/settings',
});

export const CRM_LEAD_TAB_PATHS=Object.freeze({
 Overview:'overview',
 Conversation:'conversation',
 Requirements:'requirements',
 'Property Matches':'property-matches',
 'AI & Drafts':'ai-drafts',
 'Activity & History':'activity-history',
});

const PAGE_BY_PATH=new Map(Object.entries(CRM_PAGE_PATHS).map(([page,path])=>[path,page]));
const TAB_BY_PATH=new Map(Object.entries(CRM_LEAD_TAB_PATHS).map(([tab,path])=>[path,tab]));

function validLeadId(value){
 const id=String(value??'');
 return Boolean(id&&id.length<=128&&id!=='.'&&id!=='..'&&!/[\/\\\0-\x1f\x7f]/.test(id));
}

export function buildCrmPath({page='Dashboard',leadId=null,tab='Overview'}={}){
 if(page==='Leads Inbox'&&leadId!==null&&leadId!==undefined){
  const id=String(leadId);
  if(!validLeadId(id))throw new TypeError('Invalid lead route identifier');
  const tabPath=CRM_LEAD_TAB_PATHS[tab];
  if(!tabPath)throw new TypeError('Unknown lead workspace tab');
  return '/leads/'+encodeURIComponent(id)+'/'+tabPath;
 }
 if(!Object.hasOwn(CRM_PAGE_PATHS,page))throw new TypeError('Unknown CRM page');
 if(leadId!==null&&leadId!==undefined)throw new TypeError('Lead identifier requires the Leads Inbox page');
 if(tab!=='Overview')throw new TypeError('Lead workspace tab requires a lead identifier');
 return CRM_PAGE_PATHS[page];
}

function notFound(){
 return {page:'Not Found',leadId:null,tab:'Overview',notFound:true,isRoot:false};
}

export function parseCrmPath(pathname){
 const raw=typeof pathname==='string'?pathname:'';
 const path=(raw.replace(/\/+$/,'')||'/');
 if(path==='/')return {page:'Dashboard',leadId:null,tab:'Overview',notFound:false,isRoot:true};
 const page=PAGE_BY_PATH.get(path);
 if(page)return {page,leadId:null,tab:'Overview',notFound:false,isRoot:false};

 const leadRoute=path.match(/^\/leads\/([^/]+)(?:\/([^/]+))?$/);
 if(!leadRoute)return notFound();
 let leadId;
 try{leadId=decodeURIComponent(leadRoute[1])}catch{return notFound()}
 if(!validLeadId(leadId))return notFound();
 const tabPath=leadRoute[2];
 let tab='Overview';
 if(tabPath){
  tab=TAB_BY_PATH.get(tabPath);
  if(!tab)return notFound();
 }
 return {page:'Leads Inbox',leadId,tab,notFound:false,isRoot:false};
}