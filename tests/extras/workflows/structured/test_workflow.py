import pytest
from fixpoint_extras.workflows import structured


class TestStructuredWorkflow:
    def test_workflow_declaration(self) -> None:
        with pytest.raises(Exception):

            @structured.workflow(id="workflow_without_main_task")
            class WorkflowWithoutMainTask1:
                pass

        with pytest.raises(Exception):

            @structured.workflow(id="workflow_without_main_task")
            class WorkflowWithoutMainTask2:
                @structured.task(id="my_task")
                def my_task(self, _ctx: structured.WorkflowContext) -> None:
                    pass

        with pytest.raises(Exception):

            @structured.workflow(id="two_main_tasks")
            class TwoMainTasks:
                @structured.task(id="my_task", main=True)
                def my_task(self, _ctx: structured.WorkflowContext) -> None:
                    pass

                @structured.task(id="my_task", main=True)
                def my_other_task(self, _ctx: structured.WorkflowContext) -> None:
                    pass

    def test_at_least_ctx_arg(self) -> None:
        with pytest.raises(Exception):

            @structured.workflow(id="workflow_without_main_task")
            class WorkflowWithoutMainTask:
                @structured.task(id="my_task", main=True)
                def my_task(self) -> None:
                    pass

    def test_valid_workflow(self) -> None:
        @structured.workflow(id="valid_workflow")
        class ValidWorkflow:
            @structured.task(id="my_task", main=True)
            def my_task(self) -> None:
                pass
