-- Normalize the current CRM requirement representation.
-- Tenant type is a stored requirement; the old occupancy_type field is not used.
UPDATE public.crm_leads l
SET
  tenant_type = CASE
    WHEN l.tenant_type = 'Not specified'
      AND l.requirements->>'occupancy_type' IN
        ('Family','Bachelors','Couples','Students','Working Professionals','Corporate','Other','Not specified')
    THEN l.requirements->>'occupancy_type'
    ELSE l.tenant_type
  END,
  requirements = (l.requirements - 'occupancy_type')
    || jsonb_build_object(
      'profile',
      CASE
        WHEN l.tenant_type = 'Not specified'
          AND l.requirements->>'occupancy_type' IN
            ('Family','Bachelors','Couples','Students','Working Professionals','Corporate','Other','Not specified')
        THEN l.requirements->>'occupancy_type'
        ELSE l.tenant_type
      END
    )
WHERE EXISTS (
  SELECT 1
  FROM public.crm_lead_sources s
  WHERE s.lead_id = l.id
    AND s.source_number = '+919148338801'
);
