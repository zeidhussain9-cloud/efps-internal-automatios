-- Preserve webhook messages that have no normalized contact phone (group/newsletter/unsupported senders).
-- Retry previously marked-processed events that retained a processing error but no crm_messages link.
BEGIN;

ALTER TABLE public.crm_webhook_events
  ADD COLUMN IF NOT EXISTS processing_error_history jsonb NOT NULL DEFAULT '[]'::jsonb;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='crm_webhook_events_processing_error_history_check') THEN
    ALTER TABLE public.crm_webhook_events
      ADD CONSTRAINT crm_webhook_events_processing_error_history_check
      CHECK (jsonb_typeof(processing_error_history)='array');
  END IF;
END $$;

CREATE OR REPLACE FUNCTION public.crm_process_webhook_event(
  p_event_id bigint,p_source_number text,p_phone text,p_direction text,p_message_type text,
  p_body text,p_sender_name text,p_media_urls jsonb,p_media_filenames jsonb,p_message_at timestamptz
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $function$
DECLARE
  e public.crm_webhook_events%ROWTYPE;
  c public.crm_contact_classifications%ROWTYPE;
  lead_id_value text;
  message_row public.crm_messages%ROWTYPE;
  group_chat_id text;
  group_chat_name text;
  is_group boolean := false;
  auto_group boolean := false;
BEGIN
  SELECT * INTO e FROM public.crm_webhook_events WHERE id=p_event_id FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'webhook event not found'; END IF;
  IF e.processing_status='processed' AND e.message_id IS NOT NULL THEN
    RETURN jsonb_build_object('status','processed','duplicate',true,'lead_id',e.lead_id,'message_id',e.message_id);
  END IF;
  IF p_source_number NOT IN ('+919148338801','+917975102130','+919902024973') THEN
    RAISE EXCEPTION 'unsupported source number';
  END IF;
  IF e.source_number<>p_source_number OR e.provider<>'whapi' THEN
    RAISE EXCEPTION 'webhook source/provider mismatch';
  END IF;

  group_chat_id := NULLIF(BTRIM(COALESCE(e.payload->>'chat_id','')), '');
  group_chat_name := NULLIF(BTRIM(COALESCE(e.payload->>'chat_name','')), '');
  is_group := COALESCE(RIGHT(group_chat_id,5)='@g.us', false);

  UPDATE public.crm_webhook_events
  SET processing_status='processing',
      processing_error_history=CASE WHEN processing_error IS NULL THEN processing_error_history
        ELSE processing_error_history || jsonb_build_array(jsonb_build_object('error',processing_error,'recorded_at',now(),'reconciled_at',now())) END,
      processing_error=NULL
  WHERE id=p_event_id;

  -- Never invent a contact identity for group/newsletter or otherwise unnormalizable senders.
  -- The original full provider payload remains untouched in crm_webhook_events.
  IF p_phone IS NULL THEN
    INSERT INTO public.crm_messages(
      lead_id,classification_id,source_number,provider_message_id,source_message_id,
      direction,message_type,body,sender_name,media_urls,media_filenames,message_at
    )
    VALUES(
      NULL,NULL,p_source_number,e.provider_event_id,
      COALESCE(e.provider_event_id,'whapi-event-row:'||e.id::text),
      CASE WHEN p_direction IN ('Incoming','Outgoing') THEN p_direction
           WHEN lower(COALESCE(e.payload->>'from_me','false'))='true' THEN 'Outgoing'
           ELSE 'Incoming' END,
      COALESCE(NULLIF(p_message_type,''),'text'),p_body,NULLIF(BTRIM(p_sender_name),''),
      p_media_urls,p_media_filenames,COALESCE(p_message_at,e.message_at)
    )
    ON CONFLICT DO NOTHING
    RETURNING * INTO message_row;

    IF message_row.id IS NULL THEN
      SELECT * INTO message_row
      FROM public.crm_messages
      WHERE source_number=p_source_number
        AND (provider_message_id=e.provider_event_id
             OR source_message_id='whapi-event-row:'||e.id::text)
      ORDER BY id DESC LIMIT 1;
    END IF;

    IF message_row.id IS NULL THEN RAISE EXCEPTION 'message persistence did not return a row'; END IF;

    UPDATE public.crm_webhook_events
    SET processing_status='processed',lead_id=NULL,message_id=message_row.id,
        processed_at=COALESCE(processed_at,now()),processing_error=NULL
    WHERE id=p_event_id;

    RETURN jsonb_build_object(
      'status','recorded_without_contact','duplicate',false,
      'reason','phone_unavailable','group_chat',is_group,
      'group_chat_id',group_chat_id,'group_chat_name',group_chat_name,
      'message_id',message_row.id,'classification_id',NULL,'lead_id',NULL
    );
  END IF;

  SELECT * INTO c
  FROM public.crm_contact_classifications
  WHERE source_number=p_source_number AND phone=p_phone
  FOR UPDATE;

  IF NOT FOUND THEN
    INSERT INTO public.crm_contact_classifications(
      source_number,phone,classification_code,classification_label,classification_source,
      status,evidence,first_seen_at,last_seen_at,classified_at
    )
    VALUES(
      p_source_number,p_phone,
      CASE WHEN is_group THEN 'group_message' ELSE 'pending' END,
      CASE WHEN is_group THEN 'Group Message' ELSE 'Pending classification' END,
      CASE WHEN is_group THEN 'webhook_rule' ELSE 'pending' END,
      CASE WHEN is_group THEN 'excluded' ELSE 'pending' END,
      jsonb_build_object(
        'provenance','whapi_webhook','sender_name',NULLIF(BTRIM(p_sender_name),''),
        'group_chat_id',CASE WHEN is_group THEN group_chat_id ELSE NULL END,
        'group_chat_name',CASE WHEN is_group THEN group_chat_name ELSE NULL END,
        'group_message_rule',CASE WHEN is_group THEN 'chat_id_ends_with_@g.us' ELSE NULL END
      ),
      p_message_at,p_message_at,CASE WHEN is_group THEN now() ELSE NULL END
    )
    RETURNING * INTO c;
    auto_group := is_group;
  ELSE
    UPDATE public.crm_contact_classifications
    SET last_seen_at=GREATEST(last_seen_at,p_message_at),
        evidence=evidence || jsonb_build_object(
          'sender_name',NULLIF(BTRIM(p_sender_name),''),
          'group_chat_id',CASE WHEN is_group THEN group_chat_id ELSE NULL END,
          'group_chat_name',CASE WHEN is_group THEN group_chat_name ELSE NULL END
        )
    WHERE id=c.id RETURNING * INTO c;

    IF is_group AND c.status='pending' THEN
      UPDATE public.crm_contact_classifications
      SET classification_code='group_message',classification_label='Group Message',
          classification_source='webhook_rule',confidence=NULL,status='excluded',classified_at=now(),
          evidence=evidence || jsonb_build_object(
            'group_chat_id',group_chat_id,'group_chat_name',group_chat_name,
            'group_message_rule','chat_id_ends_with_@g.us'
          )
      WHERE id=c.id RETURNING * INTO c;
      auto_group := true;
    END IF;
  END IF;

  IF auto_group THEN
    INSERT INTO public.crm_activity(lead_id,actor,action,details)
    VALUES(NULL,'webhook','contact.classified',jsonb_build_object(
      'classification_id',c.id,'phone',c.phone,'classification','group_message','status','excluded',
      'group_chat_id',group_chat_id,'group_chat_name',group_chat_name,'source_number',p_source_number
    ));
  END IF;

  -- Group messages never enter a promoted lead's personal conversation timeline.
  lead_id_value := CASE WHEN NOT is_group AND c.status='promoted' THEN c.lead_id ELSE NULL END;
  INSERT INTO public.crm_messages(
    lead_id,classification_id,source_number,provider_message_id,source_message_id,direction,
    message_type,body,sender_name,media_urls,media_filenames,message_at
  )
  VALUES(
    lead_id_value,c.id,p_source_number,e.provider_event_id,
    COALESCE(e.provider_event_id,'whapi-event-row:'||e.id::text),p_direction,
    COALESCE(NULLIF(p_message_type,''),'text'),p_body,NULLIF(BTRIM(p_sender_name),''),
    p_media_urls,p_media_filenames,COALESCE(p_message_at,e.message_at)
  )
  ON CONFLICT DO NOTHING RETURNING * INTO message_row;

  IF message_row.id IS NULL THEN
    SELECT * INTO message_row
    FROM public.crm_messages
    WHERE source_number=p_source_number
      AND (provider_message_id=e.provider_event_id
           OR source_message_id='whapi-event-row:'||e.id::text)
    ORDER BY id DESC LIMIT 1;
  END IF;
  IF message_row.id IS NULL THEN RAISE EXCEPTION 'message persistence did not return a row'; END IF;

  UPDATE public.crm_webhook_events
  SET processing_status='processed',lead_id=lead_id_value,message_id=message_row.id,
      processed_at=COALESCE(processed_at,now()),processing_error=NULL
  WHERE id=p_event_id;

  RETURN jsonb_build_object(
    'status',CASE WHEN lead_id_value IS NULL THEN 'awaiting_manual_classification' ELSE 'processed' END,
    'duplicate',false,'classification_id',c.id,'classification',c.classification_code,
    'lead_id',lead_id_value,'message_id',message_row.id
  );
END;
$function$;

REVOKE ALL ON FUNCTION public.crm_process_webhook_event(
  bigint,text,text,text,text,text,text,jsonb,jsonb,timestamptz
) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.crm_process_webhook_event(
  bigint,text,text,text,text,text,text,jsonb,jsonb,timestamptz
) TO service_role;

CREATE OR REPLACE FUNCTION public.crm_reconcile_received_webhooks()
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO ''
AS $function$
DECLARE
  e public.crm_webhook_events%ROWTYPE;
  processed_count integer := 0;
  body_text text;
BEGIN
  -- First attach any already-persisted messages, including messages without a contact phone.
  UPDATE public.crm_webhook_events AS we
  SET processing_status='processed',lead_id=m.lead_id,message_id=m.id,
      processed_at=COALESCE(we.processed_at,now()),
      processing_error_history=CASE WHEN we.processing_error IS NULL THEN we.processing_error_history
        ELSE we.processing_error_history || jsonb_build_array(jsonb_build_object('error',we.processing_error,'recorded_at',now(),'reconciled_at',now())) END,
      processing_error=NULL
  FROM public.crm_messages AS m
  WHERE we.event_type='messages'
    AND we.processing_status IN ('received','processing','processed')
    AND we.message_id IS NULL
    AND m.source_number=we.source_number
    AND ((we.provider_event_id IS NOT NULL AND m.provider_message_id=we.provider_event_id)
      OR (we.provider_event_id IS NULL AND m.source_message_id='whapi-event-row:'||we.id::text));

  FOR e IN
    SELECT * FROM public.crm_webhook_events
    WHERE source_number IN ('+919148338801','+917975102130','+919902024973')
      AND event_type='messages'
      AND (processing_status IN ('received','processing')
        OR (processing_error IS NOT NULL AND message_id IS NULL))
    ORDER BY id FOR UPDATE SKIP LOCKED
  LOOP
    body_text := COALESCE(
      CASE WHEN jsonb_typeof(e.payload->'text')='object'
        THEN NULLIF(btrim(e.payload->'text'->>'body'),'') ELSE NULL END,
      CASE WHEN jsonb_typeof(e.payload->'link_preview')='object'
        THEN NULLIF(btrim(e.payload->'link_preview'->>'body'),'') ELSE NULL END,
      NULLIF(btrim(e.payload->>'body'),'')
    );
    BEGIN
      PERFORM public.crm_process_webhook_event(
        e.id,e.source_number,e.phone,e.direction,e.message_type,
        body_text,COALESCE(e.payload->>'from_name',e.payload->>'contact_name'),
        NULL,NULL,e.message_at
      );
      processed_count := processed_count + 1;
    EXCEPTION WHEN OTHERS THEN
      UPDATE public.crm_webhook_events SET processing_error=left(SQLERRM,1000) WHERE id=e.id;
    END;
  END LOOP;
  RETURN processed_count;
END;
$function$;

REVOKE ALL ON FUNCTION public.crm_reconcile_received_webhooks() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.crm_reconcile_received_webhooks() TO postgres;

COMMIT;