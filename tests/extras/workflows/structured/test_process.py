import pytest

from fixpoint_extras.workflows.imperative import WorkflowContext
from fixpoint_extras.workflows.structured import workflow, task, entrypoint, DefinitionException
from fixpoint_extras.workflows.structured._workflow import _get_workflow_entrypoint_fixp, WorkflowEntryFixp
from fixpoint_extras.workflows.structured._task import _get_task_entrypoint_fixp, TaskEntryFixp


def test_workflow_entrypoint():
    # missing an entrypoint
    with pytest.raises(DefinitionException):
        @workflow(id="my-bad-workflow")
        class MyBadWorkflow:
            def main(self, ctx: WorkflowContext):
                pass

    @workflow(id="my-workflow")
    class MyWorkflow:
        @entrypoint()
        def main(self, ctx: WorkflowContext):
            pass

    entryfixp = _get_workflow_entrypoint_fixp(MyWorkflow.main)
    assert isinstance(entryfixp, WorkflowEntryFixp)


def test_task_entrypoint():
    # missing an entrypoint
    with pytest.raises(DefinitionException):
        @task(id="my-bad-task")
        class MyBadTask:
            def main(self, ctx: WorkflowContext):
                pass

    @task(id="my-task")
    class MyTask:
        @entrypoint()
        def main(self, ctx: WorkflowContext):
            pass

    entryfixp = _get_task_entrypoint_fixp(MyTask.main)
    assert isinstance(entryfixp, TaskEntryFixp)
