"""WorkflowRun protocol definition"""

from typing import Protocol


class WorkflowRunData(Protocol):
    """A simple data container for workflow run info.

    A simple data container for workflow run info. Technically, you could also
    pass in `fixpoint.workflows.WorkflowRun`.

    This class helps avoid circular imports.
    """

    @property
    def id(self) -> str:
        """The workflow run ID"""

    @property
    def workflow_id(self) -> str:
        """The workflow ID"""
