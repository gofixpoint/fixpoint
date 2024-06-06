"""Simple implementation of a workflow"""

from dataclasses import dataclass
from uuid import uuid4
from typing import Optional

from .protocol import SupportsWorkflow


@dataclass
class Workflow(SupportsWorkflow):
    """A simple workflow implementation"""

    name: str
    display_name: Optional[str]
    run_id: str

    def __init__(self, name: Optional[str] = None, display_name: Optional[str] = None):
        if not name:
            name = str(uuid4())
        self.name = name
        self.display_name = display_name
        self.run_id = str(uuid4())
