export const DETERMINISTIC_RULE_VERSION='1.0.0';
export const DETERMINISTIC_ACTOR='system:deterministic-classifier';

const PROPERTY_URL_RE=/(https?:\/\/(?:www\.)?(?:housing\.com|99acres\.com|magicbricks\.com)\/[^\s<]+)/i;
const MAP_URL_RE=/(https?:\/\/(?:maps\.app\.goo\.gl|goo\.gl\/maps)\/[^\s<]+)/i;
const LOCATION_RE=/\b(?:bengaluru|bangalore|hsr(?: layout)?|harlur|haralur|sarjapur(?: road)?|whitefield|bellandur|yemalur|kodathi|koramangala|indiranagar|murugeshpalya|marathahalli|kasavanahalli|kadubeesanahalli|doddakannelli|kaggadasapura|thanisandra|jayanagar|btm layout|jp nagar|electronic city|hoodi|mahadevapura|panathur|varthur|itpl|old airport road)\b/i;
const BHK_RE=/\b(?:\d+(?:\.\d+)?\s*(?:bhk|rk)|\d+(?:\.\d+)?\s*bed(?:room)?s?)\b/i;
const PROPERTY_WORD_RE=/\b(?:flat|apartment|villa|house|penthouse|row house|property|pg|co[- ]living|gated community)\b/i;
const MONEY_RE=/(?:₹|rs\.?\s*)\d[\d,]*(?:\.\d+)?\b|\b\d{1,3}(?:,\d{2,3})*(?:\.\d+)?\s*(?:k|lakh|lac)\b|\b\d{4,6}\s*(?:per month|\/month)\b/i;
const REQUIREMENT_RE=/\b(?:budget|rent|deposit|maintenance|furnished|semi[- ]furnished|unfurnished|move[- ]?in|tenant|bachelor|family|couple|student|working professional|pet|dog|cat|parking|amenit(?:y|ies)|available|availability)\b/i;
const INTENT_RE=/\b(?:looking for|looking to|i(?:'|’)m looking|i need|we need|need a|need an|want to|want a|searching for|required|require a|interested(?: in)?|please share|share some options|send options|send me|can i visit|can we visit|schedule a visit|can we see|when can we (?:visit|view|plan)|would like to|is (?:this|it) available|please let me know if.*available)\b/i;
const ACTION_INTENT_RE=/\b(?:visit|view(?:ing)?|see (?:the|this)|come (?:over|by)|schedule|can i come|can we plan)\b/i;
const NEGATIVE_INTENT_RE=/\b(?:not looking|no longer looking|not interested|already rented|found (?:a|my) tenant|found tenants|have found my tenants|wrong number|stop messaging|do not need)\b/i;
const GENERIC_RE=/^(?:hi|hello|hey|thanks|thank you|ok|okay|bro|asalamualaikum|assalamualaikum|hi zeid|hey zeid|hello zeid)[!.\s]*$/i;
const AGENT_ROLE_RE=/\b(?:i am|i'm|this is|from|represent(?:ing)?|with)\b.{0,35}\b(?:agent|broker|property dealer|real estate|channel partner)\b/i;
const AGENT_CONTEXT_RE=/\b(?:my client|client requirement|commission|brokerage|channel partner|any leads|property dealer)\b/i;
const VENDOR_ROLE_RE=/\b(?:vendor|supplier|service provider|quotation|quote for|maintenance contract|maintenance service|api (?:enabled|integration)|platform|software|agency services)\b/i;
const VENDOR_CONTEXT_RE=/\b(?:plumbing|electrician|carpenter|painting|cleaning|pest control|repair|interior|furniture|maintenance|installation|subscription|integration)\b/i;
const PROMO_ROLE_RE=/\b(?:promotion|campaign|offer|discount|deal|gift|premium|special offer|marketing|advertisement|advertising|limited time)\b/i;
const PROMO_CTA_RE=/\b(?:book|buy|apply|register|call|click|payment|avail|collaboration|partnership|we would like|greetings from|dear sir|dear madam)\b/i;
const SOCIAL_PROPERTY_URL_RE=/\b(?:facebook\.com\/(?:share\/p|groups\/)|housing\.com|99acres\.com|magicbricks\.com)\b/i;

const clean=value=>String(value??'').replace(/\s+/g,' ').trim();
const bodyOf=m=>clean(m?.body);
const incomingMessages=messages=>messages.filter(m=>m?.direction==='Incoming'&&bodyOf(m));
const outgoingMessages=messages=>messages.filter(m=>m?.direction==='Outgoing'&&bodyOf(m));
const ids=messages=>messages.map(m=>Number(m.id)).filter(Number.isInteger);
const eventIds=events=>events.map(e=>Number(e.id)).filter(Number.isInteger);
const unique=value=>[...new Set(value)];
const evidenceMessages=(messages,predicate)=>messages.filter(m=>predicate(bodyOf(m),m));
const hasAny=(messages,re)=>messages.some(m=>re.test(bodyOf(m)));

function signalNames(messages){
 const signals=[];
 if(hasAny(messages,INTENT_RE))signals.push('customer_intent_language');
 if(hasAny(messages,BHK_RE))signals.push('bhk_or_bedroom');
 if(hasAny(messages,PROPERTY_WORD_RE))signals.push('property_type_or_context');
 if(hasAny(messages,MONEY_RE))signals.push('budget_or_price');
 if(hasAny(messages,REQUIREMENT_RE))signals.push('requirement_detail');
 if(hasAny(messages,SOCIAL_PROPERTY_URL_RE))signals.push('property_source_link');
 if(hasAny(messages,LOCATION_RE))signals.push('location');
 if(hasAny(messages,PROPERTY_URL_RE))signals.push('property_listing_url');
 if(hasAny(messages,MAP_URL_RE))signals.push('map_location');
 if(hasAny(messages,ACTION_INTENT_RE))signals.push('visit_or_view_action');
 return unique(signals);
}
function groupEvidence(events){
 return events.filter(e=>{
  const p=e?.payload&&typeof e.payload==='object'?e.payload:{};
  return /@g\.us$/i.test(clean(p.chat_id??p.chatId));
 });
}
function knownIdentityCode(values=[]){
 const order=['internal','personal_family','agent_partner','vendor_supplier','group_message'];
 return order.find(code=>values.map(String).includes(code))||null;
}
function classifyAgent(incoming){
 return evidenceMessages(incoming,b=>AGENT_ROLE_RE.test(b)||AGENT_CONTEXT_RE.test(b));
}
function classifyVendor(incoming){
 const explicit=evidenceMessages(incoming,b=>VENDOR_ROLE_RE.test(b));
 return explicit.length?explicit:evidenceMessages(incoming,b=>VENDOR_CONTEXT_RE.test(b)&&/\b(?:service|quote|quotation|vendor|supplier|repair|maintenance)\b/i.test(b));
}
function classifyPromotion(incoming){
 return evidenceMessages(incoming,b=>{
  const role=PROMO_ROLE_RE.test(b),cta=PROMO_CTA_RE.test(b);
  return (role&&cta)||(/\b(?:dear sir|dear madam|greetings from)\b/i.test(b)&&/\b(?:company|campaign|collaboration|offer|promotion)\b/i.test(b));
 });
}
function customerIntentEvidence(incoming){
 return evidenceMessages(incoming,b=>!NEGATIVE_INTENT_RE.test(b)&&INTENT_RE.test(b));
}
function propertyEvidence(messages){
 return evidenceMessages(messages,b=>BHK_RE.test(b)||PROPERTY_WORD_RE.test(b)||MONEY_RE.test(b)||LOCATION_RE.test(b)||PROPERTY_URL_RE.test(b)||MAP_URL_RE.test(b)||SOCIAL_PROPERTY_URL_RE.test(b));
}
function outboundPropertyEvidence(outgoing){
 return evidenceMessages(outgoing,b=>BHK_RE.test(b)||PROPERTY_WORD_RE.test(b)||MONEY_RE.test(b)||LOCATION_RE.test(b)||PROPERTY_URL_RE.test(b)||MAP_URL_RE.test(b));
}
function coldEvidence(incoming){
 const explicit=evidenceMessages(incoming,b=>NEGATIVE_INTENT_RE.test(b));
 if(explicit.length)return explicit;
 const nonGeneric=incoming.filter(m=>!GENERIC_RE.test(bodyOf(m)));
 return incoming.length>=2&&nonGeneric.length===0?incoming:[];
}
function decision(outcome,code,reason,matches=[],webhookMatches=[],signals=[]){
 const labels={qualified_lead:'Qualified Lead',agent_partner:'Agent / Partner',vendor_supplier:'Vendor / Supplier',promotion:'Promotion / Marketing',cold_inquiry:'Cold Inquiry',internal:'Internal',personal_family:'Family / personal',group_message:'Group Message',pending:'Pending classification'};
 const rules={qualified_lead:'QUAL-02-GATES',group_message:'EXCL-01-GROUP',internal:'EXCL-02-IDENTITY-INTERNAL',personal_family:'EXCL-02-IDENTITY-PERSONAL',agent_partner:'EXCL-02-IDENTITY-AGENT',vendor_supplier:'EXCL-03-VENDOR',promotion:'EXCL-04-PROMOTION',cold_inquiry:'UNQ-01-COLD',pending:'PENDING-01-INSUFFICIENT'};
 return {outcome,classification_code:code,classification_label:labels[code]||'Pending classification',rule_id:rules[code]||'PENDING-01-INSUFFICIENT',rule_version:DETERMINISTIC_RULE_VERSION,reason,evidence_message_ids:unique(ids(matches)),evidence_webhook_event_ids:unique(eventIds(webhookMatches)),signals:unique(signals)};
}
export function classifyDeterministically({messages=[],webhookEvents=[],knownIdentityCodes=[]}={}){
 const normalized=Array.isArray(messages)?messages.filter(m=>['Incoming','Outgoing'].includes(m?.direction)&&bodyOf(m)):[];
 const incoming=incomingMessages(normalized),outgoing=outgoingMessages(normalized),groups=groupEvidence(webhookEvents);
 if(groups.length)return decision('unqualified','group_message','Persisted webhook evidence identifies a WhatsApp group chat.',[],groups,['group_chat']);
 const identity=knownIdentityCode(knownIdentityCodes);
 if(identity)return decision('unqualified',identity,'Operator-confirmed contact identity/history excludes this contact from Lead CRM.',[],[],['persistent_identity']);
 const agent=classifyAgent(incoming);
 if(agent.length)return decision('unqualified','agent_partner','Conversation contains explicit broker/agent/channel-partner evidence.',agent,[],['agent_or_broker_role']);
 const vendor=classifyVendor(incoming);
 if(vendor.length)return decision('unqualified','vendor_supplier','Conversation contains explicit vendor/service/supplier evidence.',vendor,[],['vendor_or_service_role']);
 const promotion=classifyPromotion(incoming);
 if(promotion.length)return decision('unqualified','promotion','Conversation contains multiple marketing/promotion markers.',promotion,[],['promotion_marker','marketing_call_to_action']);
 const negative=evidenceMessages(incoming,b=>NEGATIVE_INTENT_RE.test(b));
 if(negative.length)return decision('unqualified','cold_inquiry','Customer explicitly indicates they are no longer seeking the service or closes the inquiry.',negative,[],['negative_customer_intent']);
 const intent=customerIntentEvidence(incoming);
 const inboundProperty=propertyEvidence(incoming);
 const outboundProperty=outboundPropertyEvidence(outgoing);
 if(incoming.length&&intent.length&&(inboundProperty.length||outboundProperty.length)){
  const evidence=[...inboundProperty,...outboundProperty.filter(m=>!ids(inboundProperty).includes(Number(m.id)))];
  return decision('qualified','qualified_lead','Customer intent and property/requirement evidence are both established in the conversation.',evidence,[],unique([...signalNames(incoming),outboundProperty.length?'outbound_property_context':null].filter(Boolean)));
 }
 const cold=coldEvidence(incoming);
 if(cold.length)return decision('unqualified','cold_inquiry','Conversation contains enough deterministic evidence for a cold/non-qualifying inquiry.',cold,[],['insufficient_property_intent','generic_or_closed_inquiry']);
 if(outgoing.length&&!incoming.length&&outboundProperty.length)return decision('pending','pending','Outbound property/listing activity is present, but there is no customer-originated evidence to qualify or exclude the contact.',[],[],['outbound_property_context','no_inbound_customer_evidence']);
 return decision('pending','pending','Available conversation evidence is insufficient for either Qualified Lead or a supported Unqualified classification.',[],[],signalNames(normalized));
}
export function deterministicRuleSummary(){
 return {rule_version:DETERMINISTIC_RULE_VERSION,no_ai:true,generated_classifications:['qualified_lead','group_message','agent_partner','vendor_supplier','promotion','cold_inquiry'],never_generated_classifications:['property_listing_sent'],pending_is_valid_outcome:true};
}
export const DETERMINISTIC_CLASSIFICATION_POLICY={ruleVersion:DETERMINISTIC_RULE_VERSION,qualification:{gateA:'customer-side intent evidence from incoming messages',gateB:'property/requirement evidence from incoming messages or established outbound property context',requiresBoth:true},hardExclusions:['group_message','persistent_identity'],generatedUnqualified:['group_message','agent_partner','vendor_supplier','promotion','cold_inquiry'],notGenerated:['property_listing_sent'],unresolvedOutcome:'pending'};
