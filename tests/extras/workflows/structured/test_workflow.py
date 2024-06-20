import pytest
from fixpoint_extras.workflows import structured


def test_workflow_declaration() -> None:
    with pytest.raises(structured.DefinitionException):

        @structured.workflow(id="workflow_without_entrypoint")
        class WorkflowWithoutEntrypoint1:
            pass

    with pytest.raises(structured.DefinitionException):

        @structured.workflow(id="workflow_without_entrypoint")
        class WorkflowWithoutEntrypoint2:
            def main(self, _ctx: structured.WorkflowContext) -> None:
                pass

    with pytest.raises(structured.DefinitionException):

        @structured.workflow(id="two_main_tasks")
        class TwoMainTasks:
            @structured.workflow_entrypoint()
            def main(self, _ctx: structured.WorkflowContext) -> None:
                pass

            @structured.workflow_entrypoint()
            def other_main(self, _ctx: structured.WorkflowContext) -> None:
                pass

def test_at_least_ctx_arg() -> None:
    with pytest.raises(structured.DefinitionException):

        @structured.workflow(id="workflow_without_main_task")
        class WorkflowWithoutMainTask:
            @structured.workflow_entrypoint()
            def main(self) -> None:
                pass

def test_valid_workflow() -> None:
    @structured.workflow(id="valid_workflow")
    class ValidWorkflow:
        @structured.workflow_entrypoint()
        def main(self, ctx: structured.WorkflowContext) -> None:
            pass
