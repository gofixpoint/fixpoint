"""Code for agent memory"""

from dataclasses import dataclass
from typing import List, Protocol, Optional

from ..completions import ChatCompletionMessageParam, ChatCompletion
from ..workflow import SupportsWorkflow


@dataclass
class MemoryItem:
    """A single memory item"""

    messages: List[ChatCompletionMessageParam]
    completion: ChatCompletion
    workflow: Optional[SupportsWorkflow] = None


class SupportsMemory(Protocol):
    """A protocol for adding memory to an agent"""

    def memory(self) -> List[MemoryItem]:
        """Get the memory"""

    def store_memory(
        self,
        messages: List[ChatCompletionMessageParam],
        completion: ChatCompletion,
        workflow: Optional[SupportsWorkflow] = None,
    ) -> None:
        """Store the memory"""

    def to_str(self) -> str:
        """Return the formatted string of messages. Useful for printing/debugging"""


class Memory(SupportsMemory):
    """A composable class to add memory to an agent"""

    _memory: List[MemoryItem]

    def __init__(self) -> None:
        self._memory = []

    def store_memory(
        self,
        messages: List[ChatCompletionMessageParam],
        completion: ChatCompletion,
        workflow: Optional[SupportsWorkflow] = None,
    ) -> None:
        """Store the memory

        Args:
            messages (List[ChatCompletionMessageParam]): List of message parameters.
            completion (Optional[ChatCompletion]): The completion object, if any.
        """
        self._memory.append(
            MemoryItem(messages=messages, completion=completion, workflow=workflow)
        )

    def memory(self) -> List[MemoryItem]:
        """Get the memory"""
        return self._memory

    def to_str(self) -> str:
        """Return the formatted string of messages. Useful for printing/debugging"""
        delim = "============================================================"
        lines = []
        for mem in self.memory():
            lines.extend(self._format_single_mem(mem))
            lines.append(delim)
        return "\n".join(lines)

    def _format_single_mem(self, memitem: MemoryItem) -> List[str]:
        """Return the formatted string of a single memory entry"""
        messages = memitem.messages
        completion = memitem.completion
        lines = [f'{m["role"]}: {m["content"]}' for m in messages]
        lines.append(f"assistant: {completion.choices[0].message.content}")
        return lines


# Check that we implement the protocol
def _check(_c: SupportsMemory) -> None:
    pass


_check(Memory())
