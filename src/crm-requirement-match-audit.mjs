const REQUIRED_PROFILE_FIELDS=[
  'bhk','budget','preferred_locations','tenant_type','move_in_date','pets','veg_nonveg',
  'furnishing','parking','property_type','bathrooms','occupancy_count','lease_term_months',
  'preferred_floor','preferred_amenities','notes'
];

const TENANT_TYPES=new Set(['Family','Bachelors','Couples','Students','Working Professionals','Corporate','Other','Not specified']);
const PET_VALUES=new Set(['Yes','No','Unknown']);
const VEG_VALUES=new Set(['Veg','Non-Veg','No Preference','Unknown']);
const FURNISHING_VALUES=new Set(['Fully Furnished','Semi Furnished','Unfurnished','Any','Unknown']);
const PARKING_VALUES=new Set(['Required','Not Required','Any','Unknown']);

const stringValue=value=>String(value??'');
const stringArray=value=>Array.isArray(value)?value.map(stringValue):[];
const nullableNumber=value=>value===null||value===undefined||value===''?null:Number(value);

function normalizedLegacyBudget(value){
  const raw=stringValue(value);
  const stripped=raw.replace(/[^0-9.]/g,'');
  return stripped?Number(stripped):null;
}

function normalizedLegacyPets(value){
  const v=stringValue(value).toLowerCase();
  if(['yes','true'].includes(v))return'Yes';
  if(['no','false'].includes(v))return'No';
  return'Unknown';
}

function normalizedLegacyVeg(value){
  const v=stringValue(value).toLowerCase();
  if(['veg','vegetarian'].includes(v))return'Veg';
  if(['non-veg','non veg','nonveg','nonvegetarian'].includes(v))return'Non-Veg';
  if(['no preference','any'].includes(v))return'No Preference';
  return'Unknown';
}

function normalizedLegacyFurnishing(value){
  const v=stringValue(value).toLowerCase();
  if(v.includes('semi'))return'Semi Furnished';
  if(v.includes('fully'))return'Fully Furnished';
  if(v.includes('unfurn'))return'Unfurnished';
  if(['any','no preference'].includes(v))return'Any';
  return'Unknown';
}

function normalizedLegacyParking(value){
  const v=stringValue(value).toLowerCase();
  if(['required','yes','true'].includes(v))return'Required';
  if(['not required','no','false'].includes(v))return'Not Required';
  if(['any','no preference'].includes(v))return'Any';
  return'Unknown';
}

export function projectLegacyRequirementProfile(lead){
  const r=lead?.requirements&&typeof lead.requirements==='object'?lead.requirements:{};
  const locations=stringValue(r.locality||r.preferred_location);
  const amenities=Array.isArray(r.preferred_amenities)?r.preferred_amenities.map(stringValue):[];
  return{
    bhk:stringValue(r.bhk),
    budget:normalizedLegacyBudget(r.budget),
    preferred_locations:locations? [locations]:[],
    tenant_type:TENANT_TYPES.has(stringValue(lead?.tenant_type))?stringValue(lead.tenant_type):'Not specified',
    move_in_date:/^\d{4}-\d{2}-\d{2}$/.test(stringValue(r.move_in_date))?stringValue(r.move_in_date):null,
    pets:normalizedLegacyPets(r.pets??r.pet_preference),
    veg_nonveg:normalizedLegacyVeg(r.veg_nonveg),
    furnishing:normalizedLegacyFurnishing(r.furnishing),
    parking:normalizedLegacyParking(r.parking),
    property_type:stringValue(r.property_type)||'Any',
    bathrooms:stringValue(r.bathrooms),
    occupancy_count:/^\d+$/.test(stringValue(r.occupancy_count))?Number(r.occupancy_count):null,
    lease_term_months:/^\d+$/.test(stringValue(r.lease_term_months))?Number(r.lease_term_months):null,
    preferred_floor:stringValue(r.preferred_floor),
    preferred_amenities:amenities,
    notes:stringValue(r.notes)
  };
}

export function compareRequirementProfiles(actual,expected){
  const mismatches=[];
  for(const field of REQUIRED_PROFILE_FIELDS){
    const a=actual?.[field];
    const e=expected?.[field];
    const same=Array.isArray(a)||Array.isArray(e)?JSON.stringify(a??[])===JSON.stringify(e??[]):a===e;
    if(!same)mismatches.push({field,actual:a??null,expected:e??null});
  }
  return{ok:mismatches.length===0,mismatches};
}

function normalizedBhk(value){
  const matches=[...stringValue(value).matchAll(/(\d+(?:\.\d+)?)[ -]*(BHK|RK)?/gi)];
  return [...new Set(matches.map(m=>`${m[1]} ${(m[2]||'BHK').toUpperCase()}`))];
}

function normalizedLocations(value){
  return stringArray(value).flatMap(v=>v.split(/[,;|/]+/).map(x=>x.trim()).filter(x=>x.length>=2)).filter((v,i,a)=>a.indexOf(v)===i);
}

export function buildPropertyMatchingInputs(profile){
  const budget=nullableNumber(profile?.budget);
  const furnishing=stringValue(profile?.furnishing).toLowerCase().replace(/\s+/g,' ').trim();
  const furnishingValues=furnishing.includes('semi')?['Semi Furnished']:furnishing.includes('fully')?['Fully Furnished']:furnishing.includes('unfurn')?['Unfurnished']:[];
  const pet=stringValue(profile?.pets).toLowerCase().trim();
  const petValues=pet==='yes'||pet==='no'?[pet[0].toUpperCase()+pet.slice(1)]:[];
  return{
    bhkValues:normalizedBhk(profile?.bhk),
    budget:budget!==null&&Number.isFinite(budget)&&budget>=0?budget:null,
    localityValues:normalizedLocations(profile?.preferred_locations),
    furnishingValues,
    petValues
  };
}

function rowMatches(row,input){
  if(String(row?.listing_state||'')!=='Available')return false;
  if(input.bhkValues.length&&!input.bhkValues.includes(stringValue(row?.bhk)))return false;
  if(input.budget!==null&&Number(row?.monthly_rent)>input.budget)return false;
  if(input.localityValues.length&&!input.localityValues.some(v=>stringValue(row?.locality).toLowerCase().includes(v.toLowerCase())))return false;
  if(input.furnishingValues.length&&!input.furnishingValues.includes(stringValue(row?.furnishing)))return false;
  if(input.petValues.length&&!input.petValues.includes(stringValue(row?.pet_friendly)))return false;
  return true;
}

export function matchPropertyRows(rows,input){
  return (rows||[]).filter(row=>rowMatches(row,input)).sort((a,b)=>
    (Number(a?.monthly_rent)||0)-(Number(b?.monthly_rent)||0)||stringValue(a?.listing_id).localeCompare(stringValue(b?.listing_id))
  );
}

export function validatePropertyMatchInputs(input){
  const errors=[];
  if(!Array.isArray(input?.bhkValues))errors.push('bhkValues');
  if(input?.budget!==null&&(!Number.isFinite(Number(input.budget))||Number(input.budget)<0))errors.push('budget');
  if(!Array.isArray(input?.localityValues))errors.push('localityValues');
  if(!Array.isArray(input?.furnishingValues))errors.push('furnishingValues');
  if(!Array.isArray(input?.petValues))errors.push('petValues');
  return{ok:errors.length===0,errors};
}

export function auditRequirementAndMatching({qualifiedLeads=[],inventoryRows=[]}={}){
  const profileMissing=[];
  const fieldMismatches=[];
  const invalidProfiles=[];
  const invalidInputs=[];
  const matchResults=[];
  let totalMatches=0;
  let zeroMatchLeads=0;

  for(const lead of qualifiedLeads){
    const profile=lead?.profile;
    if(!profile){
      profileMissing.push(lead?.lead_id);
      continue;
    }
    const expected=projectLegacyRequirementProfile(lead);
    const comparison=compareRequirementProfiles(profile,expected);
    if(!comparison.ok)fieldMismatches.push({leadId:lead.lead_id,mismatches:comparison.mismatches});
    if(!TENANT_TYPES.has(stringValue(profile.tenant_type))||
       !PET_VALUES.has(stringValue(profile.pets))||
       !VEG_VALUES.has(stringValue(profile.veg_nonveg))||
       !FURNISHING_VALUES.has(stringValue(profile.furnishing))||
       !PARKING_VALUES.has(stringValue(profile.parking))||
       (profile.budget!==null&&(!Number.isFinite(Number(profile.budget))||Number(profile.budget)<0))||
       (profile.occupancy_count!==null&&Number(profile.occupancy_count)<=0)||
       (profile.lease_term_months!==null&&Number(profile.lease_term_months)<=0)){
      invalidProfiles.push(lead.lead_id);
    }
    const input=buildPropertyMatchingInputs(profile);
    const inputCheck=validatePropertyMatchInputs(input);
    if(!inputCheck.ok)invalidInputs.push({leadId:lead.lead_id,errors:inputCheck.errors});
    const matches=matchPropertyRows(inventoryRows,input);
    totalMatches+=matches.length;
    if(matches.length===0)zeroMatchLeads++;
    const invalidResults=matches.filter(row=>!rowMatches(row,input)).map(row=>row.listing_id);
    matchResults.push({leadId:lead.lead_id,input,matchCount:matches.length,invalidResultIds:invalidResults});
  }

  const allResultsValid=matchResults.every(x=>x.invalidResultIds.length===0);
  return{
    population:{
      qualifiedLeads:qualifiedLeads.length,
      profilesPresent:qualifiedLeads.length-profileMissing.length,
      profilesMissing:profileMissing.length
    },
    fieldCorrectness:{
      checkedProfiles:qualifiedLeads.length-profileMissing.length,
      exactLegacyProjectionMatches:(qualifiedLeads.length-profileMissing.length)-fieldMismatches.length,
      mismatchedLeads:fieldMismatches.length,
      mismatchDetails:fieldMismatches.slice(0,50),
      validProfiles:(qualifiedLeads.length-profileMissing.length)-invalidProfiles.length,
      invalidProfiles:invalidProfiles.length
    },
    matchingInputs:{
      checkedProfiles:matchResults.length,
      validInputs:matchResults.length-invalidInputs.length,
      invalidInputs:invalidInputs.length,
      invalidDetails:invalidInputs.slice(0,50)
    },
    matchingResults:{
      checkedLeads:matchResults.length,
      totalMatches,
      zeroMatchLeads,
      validResultSets:matchResults.filter(x=>x.invalidResultIds.length===0).length,
      invalidResultSets:matchResults.filter(x=>x.invalidResultIds.length>0).length,
      invalidDetails:matchResults.filter(x=>x.invalidResultIds.length>0).slice(0,50)
    },
    complete:profileMissing.length===0&&fieldMismatches.length===0&&invalidProfiles.length===0&&invalidInputs.length===0&&allResultsValid
  };
}
