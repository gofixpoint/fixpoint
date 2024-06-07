"""Simple implementation of a workflow"""

from dataclasses import dataclass

from .protocol import SupportsWorkflowRun


@dataclass
class WorkflowRun(SupportsWorkflowRun):
    """A simple workflow run implementation"""

    id: str
    workflow_id: str

    # pylint: disable=redefined-builtin
    def __init__(self, id: str, workflow_id: str):
        self.id = id
        self.workflow_id = workflow_id
