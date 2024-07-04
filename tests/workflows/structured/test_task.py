import pytest
from fixpoint.workflows import imperative
from fixpoint.workflows import structured
from fixpoint.workflows.structured._run_config import RunConfig


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
            async def main(self, _ctx: structured.WorkflowContext) -> None:
                pass

            @structured.task_entrypoint()
            async def other_main(self, _ctx: structured.WorkflowContext) -> None:
                pass


def test_at_least_ctx_arg() -> None:
    with pytest.raises(structured.DefinitionException):

        @structured.task(id="task_without_main_task")
        class taskWithoutMainTask:
            @structured.task_entrypoint()
            async def main(self) -> None:
                pass


def test_valid_task() -> None:
    @structured.task(id="valid_task")
    class Validtask:
        @structured.task_entrypoint()
        async def main(self, ctx: structured.WorkflowContext) -> None:
            pass


@pytest.mark.asyncio
async def test_call_task() -> None:
    @structured.task("my-task")
    class MyTask:
        @structured.task_entrypoint()
        async def run(self, ctx: structured.WorkflowContext, name_to_print: str) -> str:
            return f"Hello, {name_to_print}"

    workflow = imperative.Workflow(id="my-workflow")
    wrun = workflow.run()
    ctx = structured.WorkflowContext(
        run_config=RunConfig.with_in_memory(),
        agents=[],
        workflow_run=wrun,
    )
    res = await structured.call_task(ctx, MyTask.run, args=["Dylan"])
    assert res == "Hello, Dylan"


@pytest.mark.asyncio
async def test_task_cahce() -> None:
    values = {"counter": 0}

    @structured.task("my-task")
    class MyTask:
        @structured.task_entrypoint()
        async def run(self, ctx: structured.WorkflowContext, name_to_print: str) -> str:
            values["counter"] += 1
            return f"Hello, {name_to_print}"

    workflow = imperative.Workflow(id="my-workflow")
    wrun = workflow.run()
    ctx = structured.WorkflowContext(
        run_config=RunConfig.with_in_memory(),
        agents=[],
        workflow_run=wrun,
    )
    res = await structured.call_task(ctx, MyTask.run, args=["Dylan"])
    assert res == "Hello, Dylan"
    assert values["counter"] == 1

    # calling it again with the same args uses the cache
    res = await structured.call_task(ctx, MyTask.run, args=["Dylan"])
    assert res == "Hello, Dylan"
    assert values["counter"] == 1

    # calling it again with the same args uses the cache
    res = await structured.call_task(ctx, MyTask.run, args=["Jakub"])
    assert res == "Hello, Jakub"
    assert values["counter"] == 2
