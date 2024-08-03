-- migrate:up
ALTER TABLE fixpoint.workflows
ADD COLUMN org_id UUID NOT NULL;

ALTER TABLE fixpoint.chat_completion_inputs
ADD COLUMN org_id UUID NOT NULL;

ALTER TABLE fixpoint.chat_completion_outputs
ADD COLUMN org_id UUID NOT NULL;

ALTER TABLE public.memory_store
ADD COLUMN org_id UUID NOT NULL;

ALTER TABLE public.completion_cache
ADD COLUMN org_id UUID NOT NULL;

ALTER TABLE public.documents
ADD COLUMN org_id UUID NOT NULL;

ALTER TABLE public.forms_with_metadata
ADD COLUMN org_id UUID NOT NULL;

ALTER TABLE public.task_entries
ADD COLUMN org_id UUID NOT NULL;

-- migrate:down
ALTER TABLE fixpoint.workflows
DROP COLUMN org_id;

ALTER TABLE fixpoint.chat_completion_inputs
DROP COLUMN org_id;

ALTER TABLE fixpoint.chat_completion_outputs
DROP COLUMN org_id;

ALTER TABLE public.memory_store
DROP COLUMN org_id;

ALTER TABLE public.completion_cache
DROP COLUMN org_id;

ALTER TABLE public.documents
DROP COLUMN org_id;

ALTER TABLE public.forms_with_metadata
DROP COLUMN org_id;

ALTER TABLE public.task_entries
DROP COLUMN org_id;
