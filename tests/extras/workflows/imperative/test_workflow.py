from fixpoint.cache import ChatCompletionTLRUCache
from fixpoint.agents import BaseAgent
from fixpoint.agents.mock import MockAgent, new_mock_completion
from fixpoint_extras.workflows import imperative
from fixpoint_extras.workflows.imperative.workflow import NodeState
from fixpoint_extras.workflows.imperative.workflow_context import (
    _WrappedWorkflowAgents,
    WorkflowContext,
)
from fixpoint_extras.workflows.imperative._workflow_agent import WorkflowAgent


class TestNodeState:
    def test_id(self) -> None:
        node = NodeState()
        assert node.id == "/"

        node = NodeState(task="test_task", step="test_step")
        assert node.id == "/test_task/test_step"

        node = NodeState(task="test_task")
        assert node.id == "/test_task"

        node = NodeState(step="test_step")
        assert node.id == "/__main__/test_step"


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
        assert new_run.node_state is not run.node_state
        # but content is the same
        assert new_run.node_state.id == run.node_state.id

        # It's fine that workflow is the same, because we do not expect to
        # mutate it.
        assert new_run.workflow is run.workflow
