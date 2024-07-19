import pathlib
from typing import Tuple

import pytest

from fixpoint.workflows import imperative
from ...supabase_test_utils import supabase_setup_url_and_key, is_supabase_enabled


class TestWorkflowRun:
    def test_clone(self) -> None:
        workflow = imperative.Workflow(id="test_workflow")
        run = workflow.run()
        new_run = run.clone()

        # should have same docs and forms
        assert new_run.docs is run.docs
        assert new_run.forms is run.forms

        # should have same storage_config
        assert new_run.storage_config is run.storage_config

        # id should be equal
        assert new_run.id == run.id

        # should have a new node_state
        # references are different...
        assert new_run._node_state is not run._node_state
        # but content is the same
        assert new_run.current_node_info.id == run.current_node_info.id

        # It's fine that workflow is the same, because we do not expect to
        # mutate it.
        assert new_run.workflow is run.workflow

    def test_on_disk_doc_storage(self, tmp_path: pathlib.Path) -> None:
        storage_config = imperative.StorageConfig.with_disk(
            storage_path=tmp_path.as_posix(),
            agent_cache_ttl_s=60,
        )
        self.assert_doc_storage(storage_config)

    @pytest.mark.skipif(
        not is_supabase_enabled(),
        reason="Supabase must be turned on",
    )
    @pytest.mark.parametrize(
        "supabase_setup_url_and_key",
        [
            (
                f"""
        CREATE TABLE IF NOT EXISTS public.documents (
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

        TRUNCATE TABLE public.documents;
        """,
                "public.documents",
            )
        ],
        indirect=True,
    )
    def test_supabase_doc_storage(
        self, supabase_setup_url_and_key: Tuple[str, str]
    ) -> None:
        url, key = supabase_setup_url_and_key
        storage_config = imperative.StorageConfig.with_supabase(
            supabase_url=url,
            supabase_api_key=key,
        )
        self.assert_doc_storage(storage_config)

    def assert_doc_storage(self, storage_config: imperative.StorageConfig) -> None:
        workflow = imperative.Workflow(id="test_workflow")
        run = workflow.run(storage_config=storage_config)
        doc = run.docs.store(
            id="test_doc",
            contents="test_contents",
            metadata={"author": "Dylan"},
            path="task1/step2",
        )
        assert doc.workflow_id == workflow.id
        assert doc.workflow_run_id == run.id
        fetched_doc = run.docs.get(document_id="test_doc")
        assert fetched_doc is not None
        assert fetched_doc == doc

        updated_doc = run.docs.update(
            document_id="test_doc",
            contents="updated_contents",
            metadata={"author": "Jakub"},
        )

        assert doc.id == updated_doc.id
        assert doc.path == updated_doc.path
        assert doc.workflow_id == updated_doc.workflow_id
        assert doc.workflow_run_id == updated_doc.workflow_run_id
        assert doc.contents != updated_doc.contents
        assert doc.metadata != updated_doc.metadata
        assert updated_doc.contents == "updated_contents"
        assert updated_doc.metadata == {"author": "Jakub"}

        doc2 = run.docs.store(
            id="doc2",
            contents="doc 2 contents",
        )
        fetched_doc2 = run.docs.get(document_id="doc2")
        assert fetched_doc2 is not None
        assert fetched_doc2 == doc2

        assert run.docs.get(document_id="test_doc") == updated_doc
