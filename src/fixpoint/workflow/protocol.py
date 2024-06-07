"""Protocol for workflows"""

from typing import Protocol


class SupportsWorkflowRun(Protocol):
    """A protocol for a Workflow"""

    @property
    def id(self) -> str:
        """The id of the workflow run"""

    @property
    def workflow_id(self) -> str:
        """The id of the workflow"""
