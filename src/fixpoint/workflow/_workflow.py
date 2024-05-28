"""Simple implementation of a workflow"""

from dataclasses import dataclass
from uuid import uuid4
from typing import Optional

from .protocol import SupportsWorkflow


@dataclass
class Workflow(SupportsWorkflow):
    """A simple workflow implementation"""

    id: str
    display_name: Optional[str]

    def __init__(self, display_name: Optional[str] = None):
        self.id = str(uuid4())
        self.display_name = display_name
