-- migrate:up
CREATE TABLE public.task_entries(
    id TEXT PRIMARY KEY,
    task_id TEXT,
    workflow_id TEXT,
    workflow_run_id TEXT,
    status TEXT NOT NULL,
    metadata JSONB,
    source_node text,
    created_at TIMESTAMP default now(),
    updated_at TIMESTAMP default now(),
    entry_fields JSONB NOT NULL
);

-- migrate:down
DROP TABLE public.task_entries;
