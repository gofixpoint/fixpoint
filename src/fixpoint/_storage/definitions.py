"""Definitions for storage tables"""

__all__ = ["DOCS_SQLITE_TABLE", "DOCS_POSTGRES_TABLE"]

DOCS_SQLITE_TABLE = """
CREATE TABLE IF NOT EXISTS documents (
    id text PRIMARY KEY,
    workflow_id text,
    workflow_run_id text,
    path text NOT NULL,
    metadata jsonb NOT NULL,
    contents text NOT NULL,
    task text,
    step text,
    versions jsonb
);
"""

DOCS_POSTGRES_TABLE = """
CREATE TABLE if NOT EXISTS public.documents (
    id text PRIMARY KEY,
    workflow_id text,
    workflow_run_id text,
    path text NOT NULL,
    metadata jsonb NOT NULL,
    contents text NOT NULL,
    task text,
    step text,
    versions jsonb
);
"""
