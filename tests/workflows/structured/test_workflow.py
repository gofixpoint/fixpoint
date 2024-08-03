from dataclasses import dataclass
import pathlib
from typing import List, Optional, Tuple

import pytest

from fixpoint.workflows import structured


def test_workflow_declaration() -> None:
    with pytest.raises(structured.DefinitionError):

        @structured.workflow(id="workflow_without_entrypoint")
        class WorkflowWithoutEntrypoint1:
            pass

    with pytest.raises(structured.DefinitionError):

        @structured.workflow(id="workflow_without_entrypoint")
        class WorkflowWithoutEntrypoint2:
            def main(self, _ctx: structured.WorkflowContext) -> None:
                pass

    with pytest.raises(structured.DefinitionError):

        @structured.workflow(id="two_main_tasks")
        class TwoMainTasks:
            @structured.workflow_entrypoint()
            async def main(self, _ctx: structured.WorkflowContext) -> None:
                pass

            @structured.workflow_entrypoint()
            async def other_main(self, _ctx: structured.WorkflowContext) -> None:
                pass


def test_at_least_ctx_arg() -> None:
    with pytest.raises(structured.DefinitionError):

        @structured.workflow(id="workflow_without_main_task")
        class WorkflowWithoutMainTask:
            @structured.workflow_entrypoint()
            async def main(self) -> None:
                pass


def test_valid_workflow() -> None:
    @structured.workflow(id="valid_workflow")
    class ValidWorkflow:
        @structured.workflow_entrypoint()
        async def main(self, ctx: structured.WorkflowContext) -> None:
            pass


@pytest.mark.asyncio
async def test_run_workflow() -> None:
    @structured.workflow(id="workflow")
    class Workflow:
        @structured.workflow_entrypoint()
        async def main(self, ctx: structured.WorkflowContext) -> str:
            return "this is a test"

    res = await structured.run_workflow(
        Workflow.main, run_config=structured.RunConfig.with_defaults(), agents=[]
    )
    assert res == "this is a test"


@pytest.mark.asyncio
async def test_workflow_disk_durability(tmp_path: pathlib.Path) -> None:
    @structured.workflow(id="workflow")
    class Workflow:
        @structured.workflow_entrypoint()
        async def main(self, ctx: structured.WorkflowContext) -> Tuple[List[str], str]:
            task_res = await structured.call_task(ctx, FailOnceTask.main)
            step_res = await structured.call_step(ctx, from_workflow)
            return (task_res, step_res)

    task_data = {"num_runs": 0}

    @structured.task(id="fail-once")
    class FailOnceTask:
        @structured.task_entrypoint()
        async def main(self, ctx: structured.WorkflowContext) -> List[str]:
            task_data["num_runs"] += 1
            if task_data["num_runs"] == 1:
                raise Exception("fail-once failed")
            step_res = await structured.call_step(ctx, from_task)
            return ["fail-once succeeded", step_res]

    step_from_task_data = {"num_runs": 0}

    @structured.step(id="called-from-task")
    async def from_task(ctx: structured.WorkflowContext) -> str:
        step_from_task_data["num_runs"] += 1
        if step_from_task_data["num_runs"] == 1:
            raise Exception("called-from-task failed")
        return "called-from-task succeeded"

    step_from_workflow_data = {"num_runs": 0}

    @structured.step(id="called-from-workflow")
    async def from_workflow(ctx: structured.WorkflowContext) -> str:
        step_from_workflow_data["num_runs"] += 1
        if step_from_workflow_data["num_runs"] == 1:
            raise Exception("called-from-workflow failed")
        return "called-from-workflow succeeded"

    ####
    # Now we can run the workflow
    ####

    @dataclass
    class RunKwargs:
        run_id: Optional[str]

    run_kwargs = RunKwargs(run_id=None)

    async def run_workflow() -> Tuple[List[str], str]:
        run_config = structured.RunConfig.with_disk(
            storage_path=tmp_path.as_posix(),
            agent_cache_ttl_s=60 * 60,
            callcache_ttl_s=60 * 60,
        )
        if run_kwargs.run_id:
            return await structured.retry_workflow(
                Workflow.main,
                run_id=run_kwargs.run_id,
                run_config=run_config,
                agents=[],
            )
        else:
            try:
                return await structured.run_workflow(
                    Workflow.main,
                    run_config=run_config,
                    agents=[],
                )
            except structured.errors.ExecutionError as e:
                run_kwargs.run_id = e.workflow_run_id
                raise

    with pytest.raises(structured.errors.ExecutionError):
        await run_workflow()
    # We fail in the task before it can call its step, and we never reach
    # calling the other step from the workflow
    assert task_data["num_runs"] == 1
    assert step_from_task_data["num_runs"] == 0
    assert step_from_workflow_data["num_runs"] == 0

    with pytest.raises(structured.errors.ExecutionError):
        await run_workflow()
    # The task does not directly fail, but its step does.
    assert task_data["num_runs"] == 2
    assert step_from_task_data["num_runs"] == 1
    assert step_from_workflow_data["num_runs"] == 0

    with pytest.raises(structured.errors.ExecutionError):
        await run_workflow()
    # The task and its step succeed, but the other step called directly from the
    # workflow fails.
    assert task_data["num_runs"] == 3
    assert step_from_task_data["num_runs"] == 2
    assert step_from_workflow_data["num_runs"] == 1

    workflow_res = await run_workflow()
    # Everything succeeds
    assert task_data["num_runs"] == 3
    assert step_from_task_data["num_runs"] == 2
    assert step_from_workflow_data["num_runs"] == 2
