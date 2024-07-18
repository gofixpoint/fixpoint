import pathlib

from fixpoint.workflows import imperative


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

    def test_doc_storage(self, tmp_path: pathlib.Path) -> None:
        workflow = imperative.Workflow(id="test_workflow")
        run = workflow.run(
            storage_config=imperative.StorageConfig.with_disk(
                storage_path=tmp_path.as_posix(),
                agent_cache_ttl_s=60,
            )
        )
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
