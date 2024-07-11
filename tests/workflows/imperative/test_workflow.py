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
