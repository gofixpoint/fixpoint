"""Protocol for workflows"""

from typing import Optional, Protocol


class SupportsWorkflow(Protocol):
    """A protocol for a Workflow"""

    id: str
    display_name: Optional[str]
