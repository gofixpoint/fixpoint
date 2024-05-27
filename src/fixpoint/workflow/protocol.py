"""Protocol for workflows"""

from typing import Protocol


class SupportsWorkflow(Protocol):
    """A protocol for a Workflow"""

    id: str
