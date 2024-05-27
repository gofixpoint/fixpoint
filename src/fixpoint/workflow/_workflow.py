"""Simple implementation of a workflow"""

from dataclasses import dataclass

from .protocol import SupportsWorkflow


@dataclass
class Workflow(SupportsWorkflow):
    """A simple workflow implementation"""

    id: str
