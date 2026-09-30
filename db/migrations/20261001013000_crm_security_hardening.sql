-- CRM database security hardening.
-- Keep server-only CRM functions unreachable through the Supabase Data API roles,
-- and pin trigger-function name resolution to an empty search_path.

CREATE OR REPLACE FUNCTION public.crm_reject_append_only_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path TO ''
AS $$
BEGIN
  IF TG_OP = 'UPDATE'
     AND (to_jsonb(OLD) - ARRAY['lead_id','classification_id']) =
         (to_jsonb(NEW) - ARRAY['lead_id','classification_id']) THEN
    RETURN NEW;
  END IF;
  RAISE EXCEPTION 'append-only CRM record cannot be modified except lead/classification linkage';
END;
$$;

CREATE OR REPLACE FUNCTION public.crm_touch_lead_updated_at()
RETURNS trigger
LANGUAGE plpgsql
SET search_path TO ''
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

REVOKE ALL ON FUNCTION public.crm_broadcast_message_activity() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.crm_broadcast_message_activity() FROM anon, authenticated;
GRANT EXECUTE ON FUNCTION public.crm_broadcast_message_activity() TO postgres;

REVOKE ALL ON FUNCTION public.crm_reconcile_received_webhooks() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.crm_reconcile_received_webhooks() FROM anon, authenticated;
GRANT EXECUTE ON FUNCTION public.crm_reconcile_received_webhooks() TO postgres;

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
  REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
  REVOKE EXECUTE ON FUNCTIONS FROM anon, authenticated;
