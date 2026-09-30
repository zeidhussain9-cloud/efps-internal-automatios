-- CRM lead status, tenant type, and live webhook/manual-classification reconciliation
BEGIN;

ALTER TABLE public.crm_leads
  ADD COLUMN IF NOT EXISTS tenant_type text NOT NULL DEFAULT 'Not specified';

ALTER TABLE public.crm_leads DROP CONSTRAINT IF EXISTS crm_leads_tenant_type_check;
ALTER TABLE public.crm_leads ADD CONSTRAINT crm_leads_tenant_type_check
  CHECK (tenant_type IN ('Family','Bachelors','Couples','Students','Working Professionals','Corporate','Other','Not specified'));

CREATE INDEX IF NOT EXISTS crm_leads_tenant_type_idx
  ON public.crm_leads(tenant_type,updated_at DESC);

CREATE INDEX IF NOT EXISTS crm_contact_classifications_source_status_idx
  ON public.crm_contact_classifications(source_number,status,last_seen_at DESC);

COMMENT ON COLUMN public.crm_leads.lead_type IS
  'Operator-controlled Lead Status. This is the lifecycle state of an already-qualified CRM lead.';
COMMENT ON COLUMN public.crm_leads.tenant_type IS
  'Operator-controlled tenant profile such as Family, Bachelors, Couples, Students, Working Professionals or Corporate.';

-- Reconcile the SQL fallback processor with the two-layer architecture: webhook activity
-- may create a classification/message record, but never creates a CRM lead automatically.
CREATE OR REPLACE FUNCTION public.crm_process_webhook_event(
  p_event_id bigint,p_source_number text,p_phone text,p_direction text,p_message_type text,
  p_body text,p_sender_name text,p_media_urls jsonb,p_media_filenames jsonb,p_message_at timestamptz
)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $function$
DECLARE
  e public.crm_webhook_events%ROWTYPE;
  c public.crm_contact_classifications%ROWTYPE;
  lead_id_value text;
  message_row public.crm_messages%ROWTYPE;
BEGIN
  SELECT * INTO e FROM public.crm_webhook_events WHERE id=p_event_id FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'webhook event not found'; END IF;
  IF e.processing_status='processed' THEN
    RETURN jsonb_build_object('status','processed','duplicate',true,'lead_id',e.lead_id,'message_id',e.message_id);
  END IF;
  IF p_source_number NOT IN ('+919148338801','+917975102130','+919902024973') THEN
    RAISE EXCEPTION 'unsupported source number';
  END IF;
  IF e.source_number<>p_source_number OR e.provider<>'whapi' THEN
    RAISE EXCEPTION 'webhook source/provider mismatch';
  END IF;
  UPDATE public.crm_webhook_events SET processing_status='processing',processing_error=NULL WHERE id=p_event_id;

  SELECT * INTO c FROM public.crm_contact_classifications
  WHERE source_number=p_source_number AND phone=p_phone FOR UPDATE;
  IF NOT FOUND THEN
    INSERT INTO public.crm_contact_classifications(source_number,phone,classification_code,classification_label,classification_source,status,evidence,first_seen_at,last_seen_at)
    VALUES(p_source_number,p_phone,'pending','Pending classification','pending','pending',jsonb_build_object('provenance','whapi_webhook','sender_name',NULLIF(btrim(p_sender_name),'')),p_message_at,p_message_at)
    RETURNING * INTO c;
  ELSE
    UPDATE public.crm_contact_classifications
    SET last_seen_at=greatest(last_seen_at,p_message_at),
        evidence=evidence || jsonb_build_object('sender_name',NULLIF(btrim(p_sender_name),''))
    WHERE id=c.id RETURNING * INTO c;
  END IF;

  lead_id_value=CASE WHEN c.status='promoted' THEN c.lead_id ELSE NULL END;
  INSERT INTO public.crm_messages(lead_id,classification_id,source_number,provider_message_id,direction,message_type,body,sender_name,media_urls,media_filenames,message_at)
  VALUES(lead_id_value,c.id,p_source_number,e.provider_event_id,p_direction,COALESCE(NULLIF(p_message_type,''),'text'),p_body,NULLIF(btrim(p_sender_name),''),p_media_urls,p_media_filenames,p_message_at)
  ON CONFLICT DO NOTHING RETURNING * INTO message_row;

  IF message_row.id IS NULL THEN
    SELECT * INTO message_row FROM public.crm_messages
    WHERE source_number=p_source_number AND provider_message_id=e.provider_event_id LIMIT 1;
  END IF;

  UPDATE public.crm_webhook_events
  SET processing_status='processed',lead_id=lead_id_value,message_id=message_row.id,processed_at=now(),processing_error=NULL
  WHERE id=p_event_id;

  RETURN jsonb_build_object(
    'status',CASE WHEN lead_id_value IS NULL THEN 'awaiting_manual_classification' ELSE 'processed' END,
    'duplicate',false,'classification_id',c.id,'classification',c.classification_code,
    'lead_id',lead_id_value,'message_id',message_row.id
  );
END;
$function$;

REVOKE ALL ON FUNCTION public.crm_process_webhook_event(bigint,text,text,text,text,text,text,jsonb,jsonb,timestamptz) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.crm_process_webhook_event(bigint,text,text,text,text,text,text,jsonb,jsonb,timestamptz) TO service_role;

COMMIT;
