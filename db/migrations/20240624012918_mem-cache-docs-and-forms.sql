-- migrate:up
CREATE TABLE public.memory_store (
    id text PRIMARY KEY,
    agent_id text NOT NULL,
    messages jsonb NOT NULL,
    completion jsonb,
    workflow_id text,
    workflow_run_id text,
    created_at timestamp with time zone DEFAULT now()
);

CREATE INDEX idx_memory_store_agent_id ON public.memory_store (agent_id);
CREATE INDEX idx_memory_store_workflow_id ON public.memory_store (workflow_id);
CREATE INDEX idx_memory_store_workflow_run_id ON public.memory_store (workflow_run_id);


CREATE TABLE public.completion_cache (
    key text PRIMARY KEY,
    value jsonb NOT NULL,
    ttl float NOT NULL,
    expires_at float NOT NULL
);


CREATE TABLE public.documents (
    id text NOT NULL,
    workflow_id text NOT NULL,
    workflow_run_id text NOT NULL,
    path text NOT NULL,
    metadata jsonb NOT NULL,
    contents text NOT NULL,
    task text,
    step text,
    versions jsonb,
    PRIMARY KEY (id, workflow_id, workflow_run_id)
);

CREATE INDEX idx_documents_path ON public.documents (path);


CREATE TABLE public.forms_with_metadata (
    -- TODO(dbmikus) how do id and path relate?
    id text PRIMARY KEY,
    workflow_id text,
    workflow_run_id text,
    metadata jsonb,
    path text NOT NULL,
    contents jsonb NOT NULL,
    form_schema text NOT NULL,
    versions jsonb,
    task text,
    step text
);

CREATE INDEX idx_forms_workflow_run_id ON public.forms_with_metadata (workflow_run_id);
CREATE INDEX idx_forms_path ON public.forms_with_metadata (path);
CREATE INDEX idx_forms_path_2 ON public.forms_with_metadata (task, step);


-- migrate:down
DROP TABLE public.completion_cache;
DROP TABLE public.documents;
DROP TABLE public.forms_with_metadata;
