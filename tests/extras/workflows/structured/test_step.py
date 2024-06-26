from dataclasses import dataclass
import pytest
from fixpoint_extras.workflows import imperative
from fixpoint_extras.workflows import structured
from fixpoint_extras.workflows.structured._run_config import RunConfig


@dataclass
class StepArgs:
    x: int
    y: int


def test_bad_step_definition() -> None:
    # must have a ctx arg
    with pytest.raises(structured.DefinitionException):

        @structured.step(id="bad_step")
        async def bad_step() -> int:
            return 5


@pytest.mark.asyncio
async def test_bad_call_step() -> None:
    async def my_step(ctx: structured.WorkflowContext, args: StepArgs) -> int:
        return args.x + args.y

    with pytest.raises(structured.DefinitionException):
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


def new_workflow_context(workflow_id: str) -> structured.WorkflowContext:
    workflow = imperative.Workflow(id=workflow_id)
    wrun = workflow.run()
    ctx = structured.WorkflowContext(
        run_config=RunConfig.with_in_memory(),
        agents=[],
        workflow_run=wrun,
    )
    return ctx
