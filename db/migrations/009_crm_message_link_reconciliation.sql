-- Preserve append-only message content while allowing qualification linkage reconciliation.
BEGIN;
CREATE OR REPLACE FUNCTION public.crm_reject_append_only_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
BEGIN
  IF TG_OP = 'UPDATE'
     AND (to_jsonb(OLD) - ARRAY['lead_id','classification_id']) =
         (to_jsonb(NEW) - ARRAY['lead_id','classification_id']) THEN
    RETURN NEW;
  END IF;
  RAISE EXCEPTION 'append-only CRM record cannot be modified except lead/classification linkage';
END;
$function$;
COMMENT ON FUNCTION public.crm_reject_append_only_mutation() IS
'CRM messages are immutable; only lead_id and classification_id may be reconciled as contact qualification/linkage changes.';
COMMIT;
