"""Protocols for memory"""

__all__ = ["MemoryItem", "SupportsMemory"]


import datetime
import json
from typing import Iterator, List, Protocol, Optional, Any, Callable

from pydantic import BaseModel

from fixpoint._protocols.workflow_run import WorkflowRunData
from fixpoint._utils.ids import make_resource_uuid
from fixpoint.completions import ChatCompletionMessageParam, ChatCompletion


def new_memory_item_id() -> str:
    """Generate a new memory item ID"""
    return make_resource_uuid("amem")


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
    created_at: datetime.datetime

    def __init__(
        self,
        agent_id: str,
        messages: List[ChatCompletionMessageParam],
        completion: ChatCompletion[BaseModel],
        workflow_run: Optional[WorkflowRunData] = None,
        workflow_id: Optional[str] = None,
        workflow_run_id: Optional[str] = None,
        serialize_fn: Callable[[Any], str] = json.dumps,
        deserialize_fn: Callable[[str], Any] = json.loads,
        _id: Optional[str] = None,
        created_at: Optional[datetime.datetime] = None,
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
        self.created_at = created_at or datetime.datetime.now()

    def __repr__(self) -> str:
        # pylint: disable=line-too-long
        return f"MemoryItem(id={self.id}, agent_id={self.agent_id}, workflow_id={self.workflow_id}, workflow_run_id={self.workflow_run_id}, created_at={self.created_at})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MemoryItem):
            return False

        return all(
            getattr(self, attr) == getattr(other, attr)
            for attr in [
                "id",
                "agent_id",
                "workflow_id",
                "workflow_run_id",
                "messages",
                "completion",
                "created_at",
            ]
        )

    def serialize(self) -> dict[str, Any]:
        """Convert the item to a dictionary"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "messages": self._serialize_fn(self.messages),
            "completion": self.completion.serialize_json(),
            "workflow_id": self.workflow_id,
            "workflow_run_id": self.workflow_run_id,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> "MemoryItem":
        """Deserialize a dictionary into a TLRUCacheItem"""
        return cls(
            _id=data["id"],
            agent_id=data["agent_id"],
            messages=json.loads(data["messages"]),
            completion=ChatCompletion[BaseModel].deserialize_json(data["completion"]),
            workflow_id=data["workflow_id"],
            workflow_run_id=data["workflow_run_id"],
            created_at=datetime.datetime.fromisoformat(data["created_at"]),
        )


class SupportsMemory(Protocol):
    """A protocol for adding memory to an agent"""

    def memories(self) -> Iterator[MemoryItem]:
        """Get the list of memories"""

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

    def to_str(self) -> str:
        """Return the formatted string of messages. Useful for printing/debugging"""
