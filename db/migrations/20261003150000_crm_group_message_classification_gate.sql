-- CRM Group Message classification and deterministic group-chat gate
BEGIN;

ALTER TABLE public.crm_contact_classifications
  DROP CONSTRAINT IF EXISTS crm_contact_classifications_classification_code_check;

ALTER TABLE public.crm_contact_classifications
  ADD CONSTRAINT crm_contact_classifications_classification_code_check
  CHECK (classification_code IN (
    'pending',
    'qualified_lead',
    'personal_family',
    'agent_partner',
    'business',
    'promotion',
    'vendor_supplier',
    'internal',
    'cold_inquiry',
    'property_listing_sent',
    'group_message',
    'unknown'
  ));

CREATE OR REPLACE FUNCTION public.crm_process_webhook_event(
  p_event_id bigint,
  p_source_number text,
  p_phone text,
  p_direction text,
  p_message_type text,
  p_body text,
  p_sender_name text,
  p_media_urls jsonb,
  p_media_filenames jsonb,
  p_message_at timestamptz
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
  auto_grouped boolean := false;
BEGIN
  SELECT * INTO e
  FROM public.crm_webhook_events
  WHERE id=p_event_id
  FOR UPDATE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'webhook event not found';
  END IF;

  IF e.processing_status='processed' THEN
    RETURN jsonb_build_object(
      'status','processed',
      'duplicate',true,
      'lead_id',e.lead_id,
      'message_id',e.message_id
    );
  END IF;

  IF p_source_number NOT IN ('+919148338801','+917975102130','+919902024973') THEN
    RAISE EXCEPTION 'unsupported source number';
  END IF;

  IF e.source_number<>p_source_number OR e.provider<>'whapi' THEN
    RAISE EXCEPTION 'webhook source/provider mismatch';
  END IF;

  group_chat_id = NULLIF(BTRIM(COALESCE(e.payload->>'chat_id','')), '');
  group_chat_name = NULLIF(BTRIM(COALESCE(e.payload->>'chat_name','')), '');
  is_group = COALESCE(group_chat_id ~ '@g\.us$', false);

  UPDATE public.crm_webhook_events
  SET processing_status='processing',
      processing_error=NULL
  WHERE id=p_event_id;

  SELECT * INTO c
  FROM public.crm_contact_classifications
  WHERE source_number=p_source_number
    AND phone=p_phone
  FOR UPDATE;

  IF NOT FOUND THEN
    INSERT INTO public.crm_contact_classifications(
      source_number,phone,classification_code,classification_label,
      classification_source,status,evidence,first_seen_at,last_seen_at,classified_at
    )
    VALUES(
      p_source_number,
      p_phone,
      CASE WHEN is_group THEN 'group_message' ELSE 'pending' END,
      CASE WHEN is_group THEN 'Group Message' ELSE 'Pending classification' END,
      CASE WHEN is_group THEN 'webhook_rule' ELSE 'pending' END,
      CASE WHEN is_group THEN 'excluded' ELSE 'pending' END,
      jsonb_build_object(
        'provenance','whapi_webhook',
        'sender_name',NULLIF(BTRIM(p_sender_name),''),
        'group_chat_id',CASE WHEN is_group THEN group_chat_id ELSE NULL END,
        'group_chat_name',CASE WHEN is_group THEN group_chat_name ELSE NULL END,
        'group_message_rule',CASE WHEN is_group THEN 'chat_id_ends_with_@g.us' ELSE NULL END
      ),
      p_message_at,
      p_message_at,
      CASE WHEN is_group THEN now() ELSE NULL END
    )
    RETURNING * INTO c;
    auto_grouped := is_group;
  ELSE
    UPDATE public.crm_contact_classifications
    SET last_seen_at=GREATEST(last_seen_at,p_message_at),
        evidence=evidence ||
          jsonb_build_object(
            'sender_name',NULLIF(BTRIM(p_sender_name),''),
            'group_chat_id',CASE WHEN is_group THEN group_chat_id ELSE NULL END,
            'group_chat_name',CASE WHEN is_group THEN group_chat_name ELSE NULL END
          )
    WHERE id=c.id
    RETURNING * INTO c;

    IF is_group AND c.status='pending' THEN
      UPDATE public.crm_contact_classifications
      SET classification_code='group_message',
          classification_label='Group Message',
          classification_source='webhook_rule',
          confidence=NULL,
          status='excluded',
          classified_at=now(),
          evidence=evidence ||
            jsonb_build_object(
              'group_chat_id',group_chat_id,
              'group_chat_name',group_chat_name,
              'group_message_rule','chat_id_ends_with_@g.us'
            )
      WHERE id=c.id
      RETURNING * INTO c;
      auto_grouped := true;
    END IF;
  END IF;

  IF auto_grouped THEN
    INSERT INTO public.crm_activity(
      lead_id,actor,action,details
    )
    VALUES(
      NULL,
      'webhook',
      'contact.classified',
      jsonb_build_object(
        'classification_id',c.id,
        'phone',c.phone,
        'classification','group_message',
        'status','excluded',
        'group_chat_id',group_chat_id,
        'group_chat_name',group_chat_name,
        'source_number',p_source_number
      )
    );
  END IF;

  lead_id_value=CASE WHEN c.status='promoted' THEN c.lead_id ELSE NULL END;

  INSERT INTO public.crm_messages(
    lead_id,classification_id,source_number,provider_message_id,
    direction,message_type,body,sender_name,media_urls,media_filenames,message_at
  )
  VALUES(
    lead_id_value,c.id,p_source_number,e.provider_event_id,
    p_direction,
    COALESCE(NULLIF(p_message_type,''),'text'),
    p_body,
    NULLIF(BTRIM(p_sender_name),''),
    p_media_urls,p_media_filenames,p_message_at
  )
  ON CONFLICT DO NOTHING
  RETURNING * INTO message_row;

  IF message_row.id IS NULL THEN
    SELECT * INTO message_row
    FROM public.crm_messages
    WHERE source_number=p_source_number
      AND provider_message_id=e.provider_event_id
    LIMIT 1;
  END IF;

  UPDATE public.crm_webhook_events
  SET processing_status='processed',
      lead_id=lead_id_value,
      message_id=message_row.id,
      processed_at=now(),
      processing_error=NULL
  WHERE id=p_event_id;

  RETURN jsonb_build_object(
    'status',CASE WHEN lead_id_value IS NULL THEN 'awaiting_manual_classification' ELSE 'processed' END,
    'duplicate',false,
    'classification_id',c.id,
    'classification',c.classification_code,
    'lead_id',lead_id_value,
    'message_id',message_row.id
  );
END;
$function$;

REVOKE ALL ON FUNCTION public.crm_process_webhook_event(
  bigint,text,text,text,text,text,text,jsonb,jsonb,timestamptz
) FROM PUBLIC,anon,authenticated;

GRANT EXECUTE ON FUNCTION public.crm_process_webhook_event(
  bigint,text,text,text,text,text,text,jsonb,jsonb,timestamptz
) TO service_role;

COMMIT;
