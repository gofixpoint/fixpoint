"""A handle on a WorkflowRun

A handle on a WorkflowRun, which is used to check the status of a workflow run,
access its result, etc.
"""

from typing import Any, Coroutine, Optional, Protocol, cast

from .. import imperative
from ._helpers import Ret_co

Coro = Coroutine[Any, Any, Ret_co]


class WorkflowRunHandle(Protocol[Ret_co]):
    """A handle on a running workflow"""

    async def result(self) -> Ret_co:
        """The result of running a workflow"""

    def workflow_id(self) -> str:
        """The ID of the workflow"""

    def workflow_run_id(self) -> str:
        """The ID of the workflow run"""

    def finalized_workflow_run(self) -> Optional[imperative.WorkflowRun]:
        """Get the workflow run, but only after we have finished the async workflow

        This workflow run is returned as an awaitable that only resolves once
        the workflow has finished running. For the safety of the workflow, we
        don't want code outside a running workflow to have access to the
        WorkflowRun object until the workflow run is finished.
        """

    def is_open(self) -> bool:
        """Whether the workflow is running, or open but waiting before resuming.

        A workflow is open when it is actively running, or if it is suspended
        while waiting for some other event, such as a human-in-the-loop review.
        """

    def is_closed(self) -> bool:
        """Whether the workflow is closed (aka not open).

        A workflow is closed when it either succeeds, errors out, is cancelled,
        or otherwise stops.
        """


class WorkflowRunHandleImpl(WorkflowRunHandle[Ret_co]):
    """Handle to a workflow run."""

    _workflow_run: imperative.WorkflowRun
    _result: Coroutine[Any, Any, Ret_co]
    _awaited_result: Optional[Ret_co]
    _was_awaited: bool
    _is_open: bool

    def __init__(
        self, workflow_run: imperative.WorkflowRun, result: Coroutine[Any, Any, Ret_co]
    ) -> None:
        self._workflow_run = workflow_run
        self._result = result
        self._awaited_result = None
        self._was_awaited = False
        self._is_open = True

    async def result(self) -> Ret_co:
        if self._was_awaited:
            return cast(Ret_co, self._awaited_result)
        try:
            self._awaited_result = await self._result
        finally:
            self._was_awaited = True
            self._is_open = False
        return self._awaited_result

    def workflow_id(self) -> str:
        return self._workflow_run.workflow_id

    def workflow_run_id(self) -> str:
        return self._workflow_run.id

    def finalized_workflow_run(self) -> Optional[imperative.WorkflowRun]:
        if self.is_closed():
            return self._workflow_run
        return None

    def is_open(self) -> bool:
        return self._is_open

    def is_closed(self) -> bool:
        return not self.is_open()
