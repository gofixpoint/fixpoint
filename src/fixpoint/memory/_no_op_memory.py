"""A memory class that stores no memories."""

from typing import List, Optional

from pydantic import BaseModel

from fixpoint.completions import ChatCompletionMessageParam, ChatCompletion
from fixpoint._protocols.workflow_run import WorkflowRunData
from ._memory import SupportsMemory, MemoryItem


class NoOpMemory(SupportsMemory):
    """A memory class that stores no memories."""

    def memories(self) -> List[MemoryItem]:
        """Get the list of memories"""
        return []

    def store_memory(
        self,
        agent_id: str,
        messages: List[ChatCompletionMessageParam],
        completion: ChatCompletion[BaseModel],
        workflow_run: Optional[WorkflowRunData] = None,
    ) -> None:
        """Store the memory"""

    def to_str(self) -> str:
        """Return the formatted string of messages. Useful for printing/debugging"""
        return ""
