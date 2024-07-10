"""A memory class that stores no memories."""

from typing import Iterator, List, Optional

from pydantic import BaseModel

from fixpoint.completions import ChatCompletionMessageParam, ChatCompletion
from fixpoint._protocols.workflow_run import WorkflowRunData
from .protocol import SupportsMemory, MemoryItem


class NoOpMemory(SupportsMemory):
    """A memory class that stores no memories."""

    def memories(self) -> Iterator[MemoryItem]:
        """Get the list of memories"""
        yield from []

    def store_memory(
        self,
        agent_id: str,
        messages: List[ChatCompletionMessageParam],
        completion: ChatCompletion[BaseModel],
        workflow_run: Optional[WorkflowRunData] = None,
    ) -> None:
        """Store the memory"""

    def get(self, mem_id: str) -> Optional[MemoryItem]:
        """Get a memory item by ID"""
        return None

    def to_str(self) -> str:
        """Return the formatted string of messages. Useful for printing/debugging"""
        return ""
