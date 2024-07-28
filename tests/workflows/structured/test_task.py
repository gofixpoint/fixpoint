from typing import Any, Coroutine
import pytest
from fixpoint.workflows import imperative, structured, TASK_MAIN_ID, STEP_MAIN_ID
from fixpoint.workflows.structured._run_config import RunConfig

NoneCoro = Coroutine[Any, Any, None]


def test_task_declaration() -> None:
    with pytest.raises(structured.DefinitionError):

        @structured.task(id="task_without_entrypoint")
        class taskWithoutEntrypoint1:
            pass

    with pytest.raises(structured.DefinitionError):

        @structured.task(id="task_without_entrypoint")
        class taskWithoutEntrypoint2:
            def main(self, _ctx: structured.WorkflowContext) -> None:
                pass

    with pytest.raises(structured.DefinitionError):

        @structured.task(id="two_main_tasks")
        class TwoMainTasks:
            @structured.task_entrypoint()
            async def main(self, _ctx: structured.WorkflowContext) -> None:
                pass

            @structured.task_entrypoint()
            async def other_main(self, _ctx: structured.WorkflowContext) -> None:
                pass


def test_at_least_ctx_arg() -> None:
    with pytest.raises(structured.DefinitionError):

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


@pytest.mark.asyncio
async def test_task_context() -> None:

    def assert_ctx_task_step(
        ctx: structured.WorkflowContext, task: str, step: str
    ) -> None:
        assert ctx.workflow_run.node_info.task == task
        assert ctx.workflow_run.node_info.step == step

    @structured.task("task1")
    class Task1:
        @structured.task_entrypoint()
        async def run(self, ctx: structured.WorkflowContext) -> None:
            assert_ctx_task_step(ctx, "task1", STEP_MAIN_ID)
            step1_future: NoneCoro = structured.call_step(ctx, step1, args=["task1"])
            step2_future: NoneCoro = structured.call_step(ctx, step2, args=["task1"])
            assert_ctx_task_step(ctx, "task1", STEP_MAIN_ID)
            await step1_future
            assert_ctx_task_step(ctx, "task1", STEP_MAIN_ID)
            await step2_future
            assert_ctx_task_step(ctx, "task1", STEP_MAIN_ID)

    @structured.task("task2")
    class Task2:
        @structured.task_entrypoint()
        async def run(self, ctx: structured.WorkflowContext) -> None:
            assert_ctx_task_step(ctx, "task2", STEP_MAIN_ID)
            step1_future: NoneCoro = structured.call_step(ctx, step1, args=["task2"])
            step2_future: NoneCoro = structured.call_step(ctx, step2, args=["task2"])
            assert_ctx_task_step(ctx, "task2", STEP_MAIN_ID)
            await step1_future
            assert_ctx_task_step(ctx, "task2", STEP_MAIN_ID)
            await step2_future
            assert_ctx_task_step(ctx, "task2", STEP_MAIN_ID)

    @structured.step("step1")
    async def step1(ctx: structured.WorkflowContext, called_from_task: str) -> None:
        assert_ctx_task_step(ctx, called_from_task, "step1")

    @structured.step("step2")
    async def step2(ctx: structured.WorkflowContext, called_from_task: str) -> None:
        assert_ctx_task_step(ctx, called_from_task, "step2")

    @structured.workflow("workflow")
    class Workflow:
        @structured.workflow_entrypoint()
        async def run(self, ctx: structured.WorkflowContext) -> None:
            assert_ctx_task_step(ctx, TASK_MAIN_ID, STEP_MAIN_ID)
            t1_future: NoneCoro = structured.call_task(ctx, Task1.run)
            t2_future: NoneCoro = structured.call_task(ctx, Task2.run)
            assert_ctx_task_step(ctx, TASK_MAIN_ID, STEP_MAIN_ID)
            await t1_future
            assert_ctx_task_step(ctx, TASK_MAIN_ID, STEP_MAIN_ID)
            await t2_future
            assert_ctx_task_step(ctx, TASK_MAIN_ID, STEP_MAIN_ID)
