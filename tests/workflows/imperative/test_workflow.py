from fixpoint_extras.workflows.imperative.workflow import NodeState


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
