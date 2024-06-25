"""Code for agent memory"""

import json
from typing import List, Protocol, Optional, Any, Callable
import uuid

from pydantic import BaseModel

from ..completions import ChatCompletionMessageParam, ChatCompletion
from ..workflows import SupportsWorkflowRun
from ..storage.protocol import SupportsStorage


def new_memory_item_id() -> str:
    """Generate a new memory item ID"""
    return "amem-" + str(uuid.uuid4())


class MemoryItem:
    """A single memory item"""

    # The ID field is useful when identifying this resource in storage, or in a
    # future HTTP-API
    id: str
    agent_id: str
    messages: List[ChatCompletionMessageParam]
    completion: ChatCompletion[BaseModel]
    workflow_id: Optional[str] = None
    workflow_run_id: Optional[str] = None

    def __init__(
        self,
        agent_id: str,
        messages: List[ChatCompletionMessageParam],
        completion: ChatCompletion[BaseModel],
        workflow_run: Optional[SupportsWorkflowRun] = None,
        workflow_id: Optional[str] = None,
        workflow_run_id: Optional[str] = None,
        serialize_fn: Callable[[Any], str] = json.dumps,
        deserialize_fn: Callable[[str], Any] = json.loads,
        _id: Optional[str] = None,
    ) -> None:
        """
        In general, you should not pass in an ID, but it exists on the init
        function for deserializing from storage.
        """
        if workflow_run and (workflow_id or workflow_run_id):
            raise ValueError(
                'you cannot pass "workflow_run" alongside "workflow_id" or "workflow_run_id"'
            )

        self.id = _id or new_memory_item_id()
        self.agent_id = agent_id
        self.messages = messages
        self.completion = completion

        if workflow_run:
            self.workflow_id = workflow_run.workflow_id
            self.workflow_run_id = workflow_run.id
        else:
            self.workflow_id = workflow_id
            self.workflow_run_id = workflow_run_id

        self._serialize_fn = serialize_fn
        self._deserialize_fn = deserialize_fn

    def serialize(self) -> dict[str, Any]:
        """Convert the item to a dictionary"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "messages": self._serialize_fn(self.messages),
            "completion": self.completion.serialize_json(),
            "workflow_id": self.workflow_id,
            "workflow_run_id": self.workflow_run_id,
        }

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> "MemoryItem":
        """Deserialize a dictionary into a TLRUCacheItem"""

        return cls(
            _id=data.pop("id"),
            agent_id=data.pop("agent_id"),
            messages=json.loads(data.pop("messages")),
            completion=ChatCompletion[BaseModel].deserialize_json(
                data.pop("completion")
            ),
            workflow_id=data.pop("workflow_id"),
            workflow_run_id=data.pop("workflow_run_id"),
        )


class SupportsMemory(Protocol):
    """A protocol for adding memory to an agent"""

    def memories(self) -> List[MemoryItem]:
        """Get the list of memories"""

    def store_memory(
        self,
        agent_id: str,
        messages: List[ChatCompletionMessageParam],
        completion: ChatCompletion[BaseModel],
        workflow_run: Optional[SupportsWorkflowRun] = None,
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
        agent_id: str,
        messages: List[ChatCompletionMessageParam],
        completion: ChatCompletion[BaseModel],
        workflow_run: Optional[SupportsWorkflowRun] = None,
    ) -> None:
        """Store the memory

        Args:
            messages (List[ChatCompletionMessageParam]): List of message parameters.
            completion (Optional[ChatCompletion]): The completion object, if any.
        """
        mem_item = MemoryItem(
            agent_id=agent_id,
            messages=messages,
            completion=completion,
            workflow_run=workflow_run,
        )
        self._memory.append(mem_item)
        if self._storage is not None:
            self._storage.insert(mem_item)

    def memories(self) -> List[MemoryItem]:
        """Get the list of memories"""
        if self._storage is not None:
            return self._storage.fetch_latest()
        return self._memory

    def to_str(self) -> str:
        """Return the formatted string of messages. Useful for printing/debugging"""
        delim = "============================================================"
        lines = []
        for mem in self.memories():
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
