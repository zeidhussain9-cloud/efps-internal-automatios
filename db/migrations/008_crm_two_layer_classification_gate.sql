-- CRM two-layer qualification gate v1
BEGIN;

CREATE TABLE IF NOT EXISTS public.crm_contact_classifications (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source_number text NOT NULL,
  phone text NOT NULL,
  classification_code text NOT NULL DEFAULT 'pending'
    CHECK (classification_code IN ('pending','qualified_lead','personal_family','agent_partner','business','promotion','vendor_supplier','internal','cold_inquiry','property_listing_sent','unknown')),
  classification_label text NOT NULL DEFAULT 'Pending classification',
  classification_source text NOT NULL DEFAULT 'pending'
    CHECK (classification_source IN ('historical_extract','webhook_rule','operator','ai','pending')),
  confidence numeric(5,4),
  status text NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending','classified','promoted','excluded')),
  evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
  first_seen_at timestamptz NOT NULL DEFAULT now(),
  last_seen_at timestamptz NOT NULL DEFAULT now(),
  classified_at timestamptz,
  promoted_at timestamptz,
  lead_id text REFERENCES public.crm_leads(id),
  UNIQUE(source_number,phone)
);
CREATE INDEX IF NOT EXISTS crm_contact_classifications_status_idx ON public.crm_contact_classifications(status,last_seen_at DESC);
CREATE INDEX IF NOT EXISTS crm_contact_classifications_code_idx ON public.crm_contact_classifications(classification_code,last_seen_at DESC);
ALTER TABLE public.crm_contact_classifications ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.crm_contact_classifications FROM anon,authenticated;
GRANT SELECT,INSERT,UPDATE ON public.crm_contact_classifications TO service_role;

ALTER TABLE public.crm_messages ALTER COLUMN lead_id DROP NOT NULL;
ALTER TABLE public.crm_messages ADD COLUMN IF NOT EXISTS classification_id bigint REFERENCES public.crm_contact_classifications(id);
CREATE INDEX IF NOT EXISTS crm_messages_classification_idx ON public.crm_messages(classification_id,message_at ASC,id ASC);

ALTER TABLE public.crm_leads ADD COLUMN IF NOT EXISTS classification_id bigint REFERENCES public.crm_contact_classifications(id);
ALTER TABLE public.crm_leads ADD COLUMN IF NOT EXISTS lead_type text NOT NULL DEFAULT 'New';
ALTER TABLE public.crm_leads DROP CONSTRAINT IF EXISTS crm_leads_lead_type_check;
ALTER TABLE public.crm_leads ADD CONSTRAINT crm_leads_lead_type_check CHECK (lead_type IN ('New','Active Follow-up','Waiting on Customer','Waiting on Us','Nurture','Dormant','Converted','Lost','On Hold'));
CREATE INDEX IF NOT EXISTS crm_leads_lead_type_idx ON public.crm_leads(lead_type,updated_at DESC);

ALTER TABLE public.crm_webhook_events ADD COLUMN IF NOT EXISTS event_type text NOT NULL DEFAULT 'unknown';
ALTER TABLE public.crm_webhook_events ADD COLUMN IF NOT EXISTS event_fingerprint text;
ALTER TABLE public.crm_webhook_events ALTER COLUMN provider_event_id DROP NOT NULL;
ALTER TABLE public.crm_webhook_events ALTER COLUMN phone DROP NOT NULL;
ALTER TABLE public.crm_webhook_events ALTER COLUMN direction DROP NOT NULL;
UPDATE public.crm_webhook_events SET event_fingerprint = encode(extensions.digest(payload::text || ':' || received_at::text,'sha256'),'hex') WHERE event_fingerprint IS NULL;
ALTER TABLE public.crm_webhook_events ALTER COLUMN event_fingerprint SET NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS crm_webhook_events_fingerprint_idx ON public.crm_webhook_events(provider,event_fingerprint);

CREATE OR REPLACE FUNCTION public.crm_contact_classification_label(p_code text)
RETURNS text LANGUAGE sql IMMUTABLE AS $$
SELECT CASE p_code
WHEN 'qualified_lead' THEN 'Qualified Lead'
WHEN 'personal_family' THEN 'Personal / Family'
WHEN 'agent_partner' THEN 'Agent / Partner'
WHEN 'business' THEN 'Business'
WHEN 'promotion' THEN 'Promotion / Marketing'
WHEN 'vendor_supplier' THEN 'Vendor / Supplier'
WHEN 'internal' THEN 'Internal'
WHEN 'cold_inquiry' THEN 'Cold Inquiry'
WHEN 'property_listing_sent' THEN 'Property Listing Sent'
WHEN 'unknown' THEN 'Unclassified / Unknown'
ELSE 'Pending classification' END
$$;

CREATE OR REPLACE FUNCTION public.crm_normalize_classification(p_value text)
RETURNS text LANGUAGE sql IMMUTABLE AS $$
SELECT CASE lower(trim(coalesce(p_value,'')))
WHEN 'qualified lead' THEN 'qualified_lead'
WHEN 'personal/family' THEN 'personal_family'
WHEN 'personal / family' THEN 'personal_family'
WHEN 'agent/partner' THEN 'agent_partner'
WHEN 'agent / partner' THEN 'agent_partner'
WHEN 'spam/marketing' THEN 'promotion'
WHEN 'spam / marketing' THEN 'promotion'
WHEN 'promotion' THEN 'promotion'
WHEN 'business' THEN 'business'
WHEN 'vendor/supplier' THEN 'vendor_supplier'
WHEN 'vendor / supplier' THEN 'vendor_supplier'
WHEN 'internal' THEN 'internal'
WHEN 'cold inquiry' THEN 'cold_inquiry'
WHEN 'property listing sent' THEN 'property_listing_sent'
ELSE 'unknown' END
$$;

CREATE OR REPLACE FUNCTION public.crm_classify_live_text(p_body text)
RETURNS text LANGUAGE sql IMMUTABLE AS $$
SELECT CASE
WHEN coalesce(p_body,'') ~* '(unsubscribe|stop|offer|discount|sale|promotion|advertis|loan|insurance|credit card)' THEN 'promotion'
WHEN coalesce(p_body,'') ~* '(agent|broker|property dealer|realtor|channel partner)' THEN 'agent_partner'
WHEN coalesce(p_body,'') ~* '(vendor|supplier|maintenance|plumber|electrician|carpenter)' THEN 'vendor_supplier'
WHEN coalesce(p_body,'') ~* '(rent|rental|flat|apartment|room|house|villa|bhk|bedroom|property|move.?in|deposit|budget|location|locality)' THEN 'qualified_lead'
ELSE 'pending' END
$$;

CREATE OR REPLACE FUNCTION public.crm_record_whapi_event(
 p_provider text,p_event_type text,p_provider_event_id text,p_source_number text,
 p_phone text,p_direction text,p_message_type text,p_payload jsonb,p_message_at timestamptz,p_fingerprint text
)
RETURNS TABLE(event_id bigint,inserted boolean)
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
BEGIN
 IF p_provider <> 'whapi' THEN RAISE EXCEPTION 'unsupported provider'; END IF;
 IF p_source_number <> '+919148338801' THEN RAISE EXCEPTION 'unsupported source number'; END IF;
 RETURN QUERY
 WITH ins AS (
  INSERT INTO public.crm_webhook_events(provider,provider_event_id,event_type,source_number,phone,direction,message_type,payload,message_at,event_fingerprint)
  VALUES(p_provider,NULLIF(p_provider_event_id,''),COALESCE(NULLIF(p_event_type,''),'unknown'),p_source_number,p_phone,p_direction,COALESCE(NULLIF(p_message_type,''),'event'),p_payload,p_message_at,p_fingerprint)
  ON CONFLICT (provider,event_fingerprint) DO NOTHING
  RETURNING id
 )
 SELECT id,true FROM ins
 UNION ALL
 SELECT id,false FROM public.crm_webhook_events
 WHERE provider=p_provider AND event_fingerprint=p_fingerprint
 AND NOT EXISTS(SELECT 1 FROM ins);
END;
$$;
REVOKE ALL ON FUNCTION public.crm_record_whapi_event(text,text,text,text,text,text,text,jsonb,timestamptz,text) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.crm_record_whapi_event(text,text,text,text,text,text,text,jsonb,timestamptz,text) TO service_role;

CREATE OR REPLACE FUNCTION public.crm_process_whapi_message(
 p_event_id bigint,p_source_number text,p_phone text,p_direction text,p_message_type text,
 p_body text,p_sender_name text,p_media_urls jsonb,p_media_filenames jsonb,p_message_at timestamptz
)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE c public.crm_contact_classifications%ROWTYPE;
DECLARE l public.crm_leads%ROWTYPE;
DECLARE m public.crm_messages%ROWTYPE;
DECLARE code text;
DECLARE new_lead_id text;
BEGIN
 SELECT * INTO c FROM public.crm_contact_classifications
 WHERE source_number=p_source_number AND phone=p_phone FOR UPDATE;

 IF NOT FOUND THEN
  code:=public.crm_classify_live_text(p_body);
  INSERT INTO public.crm_contact_classifications(source_number,phone,classification_code,classification_label,classification_source,status,evidence,first_seen_at,last_seen_at,classified_at)
  VALUES(p_source_number,p_phone,code,public.crm_contact_classification_label(code),'webhook_rule',
    CASE WHEN code='pending' THEN 'pending' ELSE 'classified' END,
    jsonb_build_object('first_message',left(coalesce(p_body,''),1000)),
    p_message_at,p_message_at,CASE WHEN code='pending' THEN NULL ELSE p_message_at END)
  RETURNING * INTO c;
 ELSE
  UPDATE public.crm_contact_classifications SET last_seen_at=greatest(last_seen_at,p_message_at),evidence=evidence || jsonb_build_object('last_message',left(coalesce(p_body,''),1000)) WHERE id=c.id RETURNING * INTO c;
 END IF;

 IF c.classification_code <> 'qualified_lead' AND c.status <> 'promoted' THEN
  UPDATE public.crm_webhook_events SET processing_status='processed',processed_at=now(),classification_id=c.id WHERE id=p_event_id;
  RETURN jsonb_build_object('status','classified','classification',c.classification_code,'lead_id',NULL);
 END IF;

 SELECT l.* INTO l
 FROM public.crm_leads l JOIN public.crm_lead_sources s ON s.lead_id=l.id
 WHERE s.source_number=p_source_number AND s.source_contact_id=p_phone
 LIMIT 1 FOR UPDATE;

 IF NOT FOUND THEN
  new_lead_id:='L-LIVE-'||substr(encode(extensions.digest(p_source_number||chr(0)||p_phone,'sha256'),'hex'),1,20);
  INSERT INTO public.crm_leads(id,display_name,normalized_phone,status,priority,classification,classification_id,lead_type,requirements,operator_notes)
  VALUES(new_lead_id,NULLIF(btrim(p_sender_name),''),p_phone,'New','Medium','Qualified Lead',c.id,'New',jsonb_build_object('provenance','live_whatsapp','source_number',p_source_number),'')
  ON CONFLICT(id) DO NOTHING;
  INSERT INTO public.crm_lead_sources(lead_id,source_number,source_contact_id) VALUES(new_lead_id,p_source_number,p_phone) ON CONFLICT DO NOTHING;
  UPDATE public.crm_contact_classifications SET status='promoted',promoted_at=coalesce(promoted_at,now()),lead_id=new_lead_id WHERE id=c.id;
  SELECT * INTO l FROM public.crm_leads WHERE id=new_lead_id FOR UPDATE;
ELSE
  UPDATE public.crm_leads SET classification_id=c.id,classification='Qualified Lead' WHERE id=l.id;
 END IF;

 INSERT INTO public.crm_messages(lead_id,classification_id,source_number,provider_message_id,direction,message_type,body,sender_name,media_urls,media_filenames,message_at)
 VALUES(l.id,c.id,p_source_number,(SELECT provider_event_id FROM public.crm_webhook_events WHERE id=p_event_id),p_direction,COALESCE(NULLIF(p_message_type,''),'text'),p_body,NULLIF(btrim(p_sender_name),''),p_media_urls,p_media_filenames,p_message_at)
 ON CONFLICT DO NOTHING RETURNING * INTO m;

 UPDATE public.crm_webhook_events SET processing_status='processed',processed_at=now(),classification_id=c.id,lead_id=l.id,message_id=m.id WHERE id=p_event_id;
 RETURN jsonb_build_object('status','processed','classification','qualified_lead','lead_id',l.id,'message_id',m.id);
END;
$$;
REVOKE ALL ON FUNCTION public.crm_process_whapi_message(bigint,text,text,text,text,text,text,jsonb,jsonb,timestamptz) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.crm_process_whapi_message(bigint,text,text,text,text,text,jsonb,jsonb,timestamptz) TO service_role;

CREATE OR REPLACE FUNCTION public.crm_fail_webhook_event(p_event_id bigint,p_error text)
RETURNS void LANGUAGE sql SECURITY DEFINER SET search_path='' AS $$
UPDATE public.crm_webhook_events SET processing_status='failed',processing_error=left(coalesce(p_error,'unknown'),2000) WHERE id=p_event_id
$$;
REVOKE ALL ON FUNCTION public.crm_fail_webhook_event(bigint,text) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.crm_fail_webhook_event(bigint,text) TO service_role;

COMMIT;