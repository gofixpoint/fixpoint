"""Protocol for workflows"""

from typing import Protocol


class SupportsWorkflow(Protocol):
    """A protocol for a Workflow"""

    name: str

    @property
    def run_id(self) -> str:
        """The run id of the workflow"""
