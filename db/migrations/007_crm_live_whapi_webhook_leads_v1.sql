BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA extensions;

-- Live CRM is lead-only. Remove the unused staged-contact/intake model.
DROP TABLE IF EXISTS public.crm_intake_messages;
DROP TABLE IF EXISTS public.crm_intake_contacts;

CREATE TABLE IF NOT EXISTS public.crm_webhook_events (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  provider text NOT NULL,
  provider_event_id text NOT NULL,
  source_number text NOT NULL,
  phone text NOT NULL,
  direction text NOT NULL CHECK (direction IN ('Incoming','Outgoing')),
  message_type text NOT NULL DEFAULT 'text',
  payload jsonb NOT NULL,
  received_at timestamptz NOT NULL DEFAULT now(),
  message_at timestamptz NOT NULL,
  processing_status text NOT NULL DEFAULT 'received'
    CHECK (processing_status IN ('received','processing','processed','failed')),
  processing_error text,
  lead_id text REFERENCES public.crm_leads(id),
  message_id bigint REFERENCES public.crm_messages(id),
  processed_at timestamptz,
  UNIQUE (provider, provider_event_id)
);

CREATE INDEX IF NOT EXISTS crm_webhook_events_status_idx
  ON public.crm_webhook_events (processing_status, received_at, id);
CREATE INDEX IF NOT EXISTS crm_webhook_events_lead_idx
  ON public.crm_webhook_events (lead_id, message_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS crm_webhook_events_source_phone_idx
  ON public.crm_webhook_events (source_number, phone, message_at DESC, id DESC);

ALTER TABLE public.crm_webhook_events ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.crm_webhook_events FROM anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON TABLE public.crm_webhook_events TO service_role;

CREATE OR REPLACE FUNCTION public.crm_get_webhook_secret()
RETURNS text LANGUAGE sql SECURITY DEFINER SET search_path = '' AS $$
  SELECT decrypted_secret
  FROM vault.decrypted_secrets
  WHERE name = 'crm_whapi_webhook_token'
  LIMIT 1
$$;
REVOKE ALL ON FUNCTION public.crm_get_webhook_secret() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.crm_get_webhook_secret() TO service_role;

CREATE OR REPLACE FUNCTION public.crm_record_webhook_event(
  p_provider text,
  p_provider_event_id text,
  p_source_number text,
  p_phone text,
  p_direction text,
  p_message_type text,
  p_payload jsonb,
  p_message_at timestamptz
)
RETURNS TABLE (event_id bigint, inserted boolean, processing_status text, lead_id text, message_id bigint)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
  IF p_source_number <> '+919148338801' THEN RAISE EXCEPTION 'unsupported source number'; END IF;
  IF p_provider <> 'whapi' THEN RAISE EXCEPTION 'unsupported provider'; END IF;
  IF p_direction NOT IN ('Incoming','Outgoing') THEN RAISE EXCEPTION 'invalid direction'; END IF;
  RETURN QUERY
  WITH inserted_row AS (
    INSERT INTO public.crm_webhook_events AS we
      (provider,provider_event_id,source_number,phone,direction,message_type,payload,message_at)
    VALUES
      (p_provider,p_provider_event_id,p_source_number,p_phone,p_direction,COALESCE(NULLIF(p_message_type,''),'text'),p_payload,p_message_at)
    ON CONFLICT (provider,provider_event_id) DO NOTHING
    RETURNING we.id AS event_id,true AS was_inserted,we.processing_status AS row_status,we.lead_id AS row_lead_id,we.message_id AS row_message_id
  )
  SELECT ir.event_id,ir.was_inserted,ir.row_status,ir.row_lead_id,ir.row_message_id FROM inserted_row ir
  UNION ALL
  SELECT we.id,false,we.processing_status,we.lead_id,we.message_id
  FROM public.crm_webhook_events we
  WHERE we.provider=p_provider AND we.provider_event_id=p_provider_event_id
    AND NOT EXISTS (SELECT 1 FROM inserted_row);
END;
$$;
REVOKE ALL ON FUNCTION public.crm_record_webhook_event(text,text,text,text,text,text,jsonb,timestamptz) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.crm_record_webhook_event(text,text,text,text,text,text,jsonb,timestamptz) TO service_role;

CREATE OR REPLACE FUNCTION public.crm_process_webhook_event(
  p_event_id bigint,p_source_number text,p_phone text,p_direction text,p_message_type text,
  p_body text,p_sender_name text,p_media_urls jsonb,p_media_filenames jsonb,p_message_at timestamptz
)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE
  e public.crm_webhook_events%ROWTYPE;
  lead_row public.crm_leads%ROWTYPE;
  message_row public.crm_messages%ROWTYPE;
  lead_id_value text;
BEGIN
  SELECT * INTO e FROM public.crm_webhook_events WHERE id=p_event_id FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'webhook event not found'; END IF;
  IF e.processing_status='processed' THEN
    RETURN jsonb_build_object('status','processed','duplicate',true,'lead_id',e.lead_id,'message_id',e.message_id);
  END IF;
  IF e.source_number<>'+919148338801' OR p_source_number<>'+919148338801' THEN RAISE EXCEPTION 'unsupported source number'; END IF;
  UPDATE public.crm_webhook_events SET processing_status='processing',processing_error=NULL WHERE id=p_event_id;

  SELECT l.* INTO lead_row
  FROM public.crm_leads l JOIN public.crm_lead_sources s ON s.lead_id=l.id
  WHERE s.source_number=p_source_number AND s.source_contact_id=p_phone
  LIMIT 1 FOR UPDATE OF l;

  IF FOUND THEN
    lead_id_value:=lead_row.id;
  ELSE
    lead_id_value:='L-LIVE-'||substr(encode(digest(p_source_number||chr(0)||p_phone,'sha256'),'hex'),1,20);
    INSERT INTO public.crm_leads(id,display_name,normalized_phone,status,priority,classification,requirements,operator_notes)
    VALUES(lead_id_value,NULLIF(btrim(p_sender_name),''),p_phone,'New','Medium',NULL,
      jsonb_build_object('provenance','live_whatsapp','source_number',p_source_number),'')
    ON CONFLICT (id) DO NOTHING;
    INSERT INTO public.crm_lead_sources(lead_id,source_number,source_contact_id)
    VALUES(lead_id_value,p_source_number,p_phone) ON CONFLICT DO NOTHING;
    SELECT l.* INTO lead_row FROM public.crm_leads l WHERE l.id=lead_id_value FOR UPDATE;
  END IF;

  IF NULLIF(btrim(p_sender_name),'') IS NOT NULL AND NULLIF(btrim(lead_row.display_name),'') IS NULL THEN
    UPDATE public.crm_leads SET display_name=btrim(p_sender_name),updated_at=now() WHERE id=lead_id_value;
  END IF;

  INSERT INTO public.crm_messages(lead_id,source_number,provider_message_id,direction,message_type,body,sender_name,media_urls,media_filenames,message_at)
  VALUES(lead_id_value,p_source_number,e.provider_event_id,p_direction,COALESCE(NULLIF(p_message_type,''),'text'),p_body,NULLIF(btrim(p_sender_name),''),p_media_urls,p_media_filenames,p_message_at)
  ON CONFLICT DO NOTHING RETURNING * INTO message_row;

  IF message_row.id IS NULL THEN
    SELECT * INTO message_row FROM public.crm_messages
    WHERE source_number=p_source_number AND provider_message_id=e.provider_event_id LIMIT 1;
  END IF;

  UPDATE public.crm_webhook_events SET processing_status='processed',lead_id=lead_id_value,message_id=message_row.id,processed_at=now(),processing_error=NULL WHERE id=p_event_id;
  IF message_row.id IS NOT NULL THEN
    INSERT INTO public.crm_activity(lead_id,actor,action,details)
    VALUES(lead_id_value,'whatsapp-webhook','message.received',jsonb_build_object('source_number',p_source_number,'provider','whapi','provider_message_id',e.provider_event_id,'webhook_event_id',p_event_id));
  END IF;
  RETURN jsonb_build_object('status','processed','duplicate',false,'lead_id',lead_id_value,'message_id',message_row.id);
END;
$$;
REVOKE ALL ON FUNCTION public.crm_process_webhook_event(bigint,text,text,text,text,text,text,jsonb,jsonb,timestamptz) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.crm_process_webhook_event(bigint,text,text,text,text,text,text,jsonb,jsonb,timestamptz) TO service_role;

CREATE OR REPLACE FUNCTION public.crm_fail_webhook_event(p_event_id bigint,p_error text)
RETURNS void LANGUAGE sql SECURITY DEFINER SET search_path = '' AS $$
  UPDATE public.crm_webhook_events
  SET processing_status='failed',processing_error=left(coalesce(p_error,'unknown webhook processing error'),2000)
  WHERE id=p_event_id
$$;
REVOKE ALL ON FUNCTION public.crm_fail_webhook_event(bigint,text) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.crm_fail_webhook_event(bigint,text) TO service_role;

CREATE OR REPLACE FUNCTION public.crm_broadcast_message_activity()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
  PERFORM realtime.send(jsonb_build_object('kind','crm_message_activity'),'message_inserted','crm:live',false);
  RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS crm_messages_realtime_broadcast ON public.crm_messages;
CREATE TRIGGER crm_messages_realtime_broadcast AFTER INSERT ON public.crm_messages
FOR EACH ROW EXECUTE FUNCTION public.crm_broadcast_message_activity();

COMMIT;
