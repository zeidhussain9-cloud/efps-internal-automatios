BEGIN;
CREATE TABLE IF NOT EXISTS public.crm_ai_cursors_v2(
 lead_id text PRIMARY KEY REFERENCES public.crm_leads(id) ON DELETE RESTRICT,
 source_number text NOT NULL,
 last_message_id bigint,
 last_message_at timestamptz,
 updated_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO public.crm_ai_cursors_v2(lead_id,source_number,last_message_at)
SELECT l.id,s.source_number,c.last_message_at
FROM public.crm_leads l JOIN LATERAL (SELECT source_number FROM public.crm_lead_sources WHERE lead_id=l.id ORDER BY source_number LIMIT 1) s ON true
LEFT JOIN public.crm_ai_cursors c ON c.source_number=s.source_number
ON CONFLICT(lead_id) DO NOTHING;
DROP TABLE IF EXISTS public.crm_ai_cursors;
ALTER TABLE public.crm_ai_cursors_v2 RENAME TO crm_ai_cursors;
ALTER TABLE public.crm_ai_cursors ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.crm_ai_cursors FROM anon,authenticated;
INSERT INTO public.crm_schema_migrations(version) VALUES(15) ON CONFLICT DO NOTHING;
COMMIT;
