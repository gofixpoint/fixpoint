import asyncio
from dataclasses import dataclass
import pytest
from fixpoint.workflows import imperative, structured, TASK_MAIN_ID, STEP_MAIN_ID
from fixpoint.workflows.structured._run_config import RunConfig


@dataclass
class StepArgs:
    x: int
    y: int


def test_bad_step_definition() -> None:
    # must have a ctx arg
    with pytest.raises(structured.DefinitionError):

        @structured.step(id="bad_step")
        async def bad_step() -> int:
            return 5


@pytest.mark.asyncio
async def test_bad_call_step() -> None:
    async def my_step(ctx: structured.WorkflowContext, args: StepArgs) -> int:
        return args.x + args.y

    with pytest.raises(structured.DefinitionError):
        await structured.call_step(
            new_workflow_context("my-workflow"),
            my_step,
            args=[StepArgs(x=1, y=2)],
        )


@pytest.mark.asyncio
async def test_run_step() -> None:
    @structured.step(id="my_step")
    async def my_step(ctx: structured.WorkflowContext, args: StepArgs) -> int:
        return args.x + args.y

    ctx = new_workflow_context("my-workflow")
    res = await structured.call_step(ctx, my_step, args=[StepArgs(x=1, y=2)])
    assert res == 3


@pytest.mark.asyncio
async def test_step_cache() -> None:
    values = {"counter": 0}

    @structured.step(id="my_step")
    async def my_step(ctx: structured.WorkflowContext, args: StepArgs) -> int:
        values["counter"] += 1
        return args.x + args.y

    ctx = new_workflow_context("my-workflow")
    res = await structured.call_step(ctx, my_step, args=[StepArgs(x=1, y=2)])
    assert res == 3
    assert values["counter"] == 1

    # calling it with same args uses the cached result
    res = await structured.call_step(ctx, my_step, args=[StepArgs(x=1, y=2)])
    assert res == 3
    assert values["counter"] == 1

    # calling it with same args uses the cached result
    res = await structured.call_step(ctx, my_step, args=[StepArgs(x=10, y=2)])
    assert res == 12
    assert values["counter"] == 2


@pytest.mark.asyncio
async def test_step_context() -> None:
    ctx = new_workflow_context("my-workflow")

    def assert_ctx_main(ctx: structured.WorkflowContext) -> None:
        assert ctx.workflow_run.node_info.task == TASK_MAIN_ID
        assert ctx.workflow_run.node_info.step == STEP_MAIN_ID

    assert_ctx_main(ctx)

    @structured.step(id="step1")
    async def step1(ctx: structured.WorkflowContext) -> None:
        assert ctx.workflow_run.node_info.task == TASK_MAIN_ID
        assert ctx.workflow_run.node_info.step == "step1"

    @structured.step(id="step2")
    async def step2(ctx: structured.WorkflowContext) -> None:
        assert ctx.workflow_run.node_info.task == TASK_MAIN_ID
        assert ctx.workflow_run.node_info.step == "step2"

    s1_future = structured.call_step(ctx, step1)
    s2_future = structured.call_step(ctx, step2)
    assert_ctx_main(ctx)
    await s1_future
    assert_ctx_main(ctx)
    await s2_future
    assert_ctx_main(ctx)


def new_workflow_context(workflow_id: str) -> structured.WorkflowContext:
    workflow = imperative.Workflow(id=workflow_id)
    wrun = workflow.run()
    ctx = structured.WorkflowContext(
        run_config=RunConfig.with_in_memory(),
        agents=[],
        workflow_run=wrun,
    )
    return ctx
