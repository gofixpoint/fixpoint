"""Simple implementation of a workflow"""

from dataclasses import dataclass

from .protocol import SupportsWorkflowRun


@dataclass
class WorkflowRun(SupportsWorkflowRun):
    """A simple workflow run implementation"""

    _id: str
    _workflow_id: str

    # pylint: disable=redefined-builtin
    def __init__(self, id: str, workflow_id: str):
        self._id = id
        self._workflow_id = workflow_id

    @property
    def id(self) -> str:
        return self._id

    @property
    def workflow_id(self) -> str:
        return self._workflow_id
