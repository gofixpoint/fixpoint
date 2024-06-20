import pytest
from fixpoint_extras.workflows import structured


def test_task_declaration() -> None:
    with pytest.raises(structured.DefinitionException):

        @structured.task(id="task_without_entrypoint")
        class taskWithoutEntrypoint1:
            pass

    with pytest.raises(structured.DefinitionException):

        @structured.task(id="task_without_entrypoint")
        class taskWithoutEntrypoint2:
            def main(self, _ctx: structured.WorkflowContext) -> None:
                pass

    with pytest.raises(structured.DefinitionException):

        @structured.task(id="two_main_tasks")
        class TwoMainTasks:
            @structured.task_entrypoint()
            def main(self, _ctx: structured.WorkflowContext) -> None:
                pass

            @structured.task_entrypoint()
            def other_main(self, _ctx: structured.WorkflowContext) -> None:
                pass

def test_at_least_ctx_arg() -> None:
    with pytest.raises(structured.DefinitionException):

        @structured.task(id="task_without_main_task")
        class taskWithoutMainTask:
            @structured.task_entrypoint()
            def main(self) -> None:
                pass

def test_valid_task() -> None:
    @structured.task(id="valid_task")
    class Validtask:
        @structured.task_entrypoint()
        def main(self, ctx: structured.WorkflowContext) -> None:
            pass
