-- migrate:up
CREATE TABLE public.workflow_tasks(
    id TEXT PRIMARY KEY,
    workflow_id TEXT,
    workflow_run_id TEXT,
    status TEXT NOT NULL,
    created_at TIMESTAMP default now(),
    updated_at TIMESTAMP default now(),
    entry_fields JSONB NOT NULL
);

-- migrate:down
DROP TABLE public.workflow_tasks;
