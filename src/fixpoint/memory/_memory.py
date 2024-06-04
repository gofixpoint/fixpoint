"""Code for agent memory"""

from typing import List, Protocol, Optional, Any, Callable
import json

from pydantic import BaseModel

from ..completions import ChatCompletionMessageParam, ChatCompletion
from ..workflow import SupportsWorkflow
from ..storage.protocol import SupportsStorage


class MemoryItem:
    """A single memory item"""

    messages: List[ChatCompletionMessageParam]
    completion: ChatCompletion[BaseModel]
    workflow: Optional[SupportsWorkflow] = None

    def __init__(
        self,
        messages: List[ChatCompletionMessageParam],
        completion: ChatCompletion[BaseModel],
        workflow: Optional[SupportsWorkflow] = None,
        serialize_fn: Callable[[Any], str] = json.dumps,
        deserialize_fn: Callable[[str], Any] = json.loads,
    ) -> None:
        self.messages = messages
        self.completion = completion
        self.workflow = workflow
        self._serialize_fn = serialize_fn
        self._deserialize_fn = deserialize_fn

    def serialize(self) -> dict[str, Any]:
        """Convert the item to a dictionary"""
        return {
            "messages": self._serialize_fn(self.messages),
            "completion": self.completion.serialize_json(),
            "workflow": self._serialize_fn(self.workflow),
        }

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> "MemoryItem":
        """Deserialize a dictionary into a TLRUCacheItem"""

        messages = json.loads(data.pop("messages"))
        completion = ChatCompletion[BaseModel].deserialize_json(data.pop("completion"))
        workflow = json.loads(data.pop("workflow"))
        return cls(messages=messages, completion=completion, workflow=workflow)


class SupportsMemory(Protocol):
    """A protocol for adding memory to an agent"""

    def memory(self) -> List[MemoryItem]:
        """Get the memory"""

    def store_memory(
        self,
        messages: List[ChatCompletionMessageParam],
        completion: ChatCompletion[BaseModel],
        workflow: Optional[SupportsWorkflow] = None,
    ) -> None:
        """Store the memory"""

    def to_str(self) -> str:
        """Return the formatted string of messages. Useful for printing/debugging"""


class Memory(SupportsMemory):
    """A composable class to add memory to an agent"""

    _memory: List[MemoryItem]
    _storage: Optional[SupportsStorage[MemoryItem]]

    def __init__(self, storage: Optional[SupportsStorage[MemoryItem]] = None) -> None:
        self._memory = []
        self._storage = storage

    def store_memory(
        self,
        messages: List[ChatCompletionMessageParam],
        completion: ChatCompletion[BaseModel],
        workflow: Optional[SupportsWorkflow] = None,
    ) -> None:
        """Store the memory

        Args:
            messages (List[ChatCompletionMessageParam]): List of message parameters.
            completion (Optional[ChatCompletion]): The completion object, if any.
        """
        mem_item = MemoryItem(
            messages=messages, completion=completion, workflow=workflow
        )
        self._memory.append(mem_item)
        if self._storage is not None:
            self._storage.insert(mem_item)

    def memory(self) -> List[MemoryItem]:
        """Get the memory"""
        if self._storage is not None:
            return self._storage.fetch_latest()
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
