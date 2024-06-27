"""A handle on a WorkflowRun

A handle on a WorkflowRun, which is used to check the status of a workflow run,
access its result, etc.
"""

from typing import Protocol

from .. import imperative
from ._helpers import Ret_co


class WorkflowRunHandle(Protocol[Ret_co]):
    """A handle on a running workflow"""

    def result(self) -> Ret_co:
        """The result of running a workflow"""

    def workflow_id(self) -> str:
        """The ID of the workflow"""

    def workflow_run_id(self) -> str:
        """The ID of the workflow run"""


class WorkflowRunHandleImpl(WorkflowRunHandle[Ret_co]):
    """Handle to a workflow run."""

    _workflow_run: imperative.WorkflowRun
    _result: Ret_co

    def __init__(self, workflow_run: imperative.WorkflowRun, result: Ret_co) -> None:
        self._workflow_run = workflow_run
        self._result = result

    def result(self) -> Ret_co:
        return self._result

    def workflow_id(self) -> str:
        return self._workflow_run.workflow_id

    def workflow_run_id(self) -> str:
        return self._workflow_run.id
