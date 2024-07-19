"""
Node state management for workflows.
"""

__all__ = ["WorkflowStatus", "NodeInfo", "CallHandle", "NodeState", "SpawnGroup"]

import threading
from enum import Enum
from types import TracebackType
from typing import List, Optional, Callable, Union
from pydantic import BaseModel, Field, computed_field, PrivateAttr

from fixpoint.workflows.constants import TASK_MAIN_ID, STEP_MAIN_ID


class WorkflowStatus(Enum):
    """The status of a node within the workflow"""

    RUNNING = "RUNNING"  # OPEN
    SUSPENDED = "SUSPENDED"  # OPEN
    FAILED = "FAILED"  # CLOSED
    CANCELLED = "CANCELLED"  # CLOSED
    COMPLETED = "COMPLETED"  # CLOSED
    TERMINATED = "TERMINATED"  # CLOSED
    TIMED_OUT = "TIMED_OUT"  # CLOSED
    CONTINUED_AS_NEW = "CONTINUED_AS_NEW"  # CLOSED


class NodeInfo(BaseModel):
    """
    Each task or step in a workflow run is a "node". This keeps track of which
    node the workflow run is in.
    """

    task: str = Field(description="The task that the node is in", default=TASK_MAIN_ID)
    step: str = Field(description="The step that the node is in", default=STEP_MAIN_ID)
    status: Optional[WorkflowStatus] = Field(
        description="The status of the node", default=WorkflowStatus.RUNNING
    )

    @computed_field  # type: ignore[misc]
    @property
    def id(self) -> str:
        """The node's identifier within the workflow run"""
        return f"{self.task}/{self.step}"


class CallHandle:
    """A handle used for transitioning back to the parent state"""

    _current_state: "NodeState"
    _update_node_state: Optional[Callable[["NodeState"], "NodeState"]]

    def __init__(
        self,
        current_state: "NodeState",
        update_node_state: Optional[Callable[["NodeState"], "NodeState"]] = None,
    ):
        self._current_state = current_state
        self._update_node_state = update_node_state

    def close(self, status: WorkflowStatus) -> "NodeState":
        """Close the node and return the parent state"""
        # Set status on current node and return parent state
        self._current_state.info.status = status
        prev_state = self._current_state.prev_state
        if prev_state is None:
            raise RuntimeError("Cannot close node with no previous state")
        if self._update_node_state is not None:
            self._update_node_state(prev_state)
        return prev_state


class NodeState(BaseModel):
    """The state of a node in a workflow run"""

    prev_state: Optional["NodeState"] = Field(
        description="The previous state", default=None
    )
    info: NodeInfo = Field(description="The head of the node state", default=NodeInfo())
    next_states: List["NodeState"] = Field(description="The next states", default=[])
    _lock: threading.Lock = PrivateAttr(default_factory=threading.Lock)

    def _add_node(self, step: str, task: str) -> "NodeState":
        next_state = NodeState(info=NodeInfo(step=step, task=task), prev_state=self)
        self.next_states.append(next_state)
        return next_state

    def add_step(self, step: str, task: Union[str, None] = None) -> "NodeState":
        """Add a step to the node state"""
        with self._lock:  # pylint: disable=not-context-manager
            task = task or self.info.task
            return self._add_node(step, task)

    def add_task(self, task: str) -> "NodeState":
        """Add a task to the node state"""
        with self._lock:  # pylint: disable=not-context-manager
            return self._add_node(STEP_MAIN_ID, task)


class SpawnGroup:
    """Context manager for spawning nodes in a group"""

    _node_state: NodeState
    _spawned_nodes: List[NodeState]

    def __init__(self, node_state: NodeState):
        self._node_state = node_state
        self._spawned_nodes = []

    def __enter__(self) -> "SpawnGroup":
        return self

    def __exit__(
        self,
        exc_type: Union[type[BaseException], None],
        exc_val: Union[BaseException, None],
        exc_tb: Union[TracebackType, None],
    ) -> None:
        if exc_val is not None:
            for node in self._spawned_nodes:
                node.info.status = WorkflowStatus.FAILED
        else:
            for node in self._spawned_nodes:
                node.info.status = WorkflowStatus.COMPLETED

    def spawn_task(self, task: str) -> CallHandle:
        """Spawn a task"""
        # Spawn a task, but don't change a node state
        new_node = self._node_state.add_task(task)
        self._spawned_nodes.append(new_node)
        return CallHandle(new_node)

    def spawn_step(self, step: str) -> CallHandle:
        """Spawn a step"""
        new_node = self._node_state.add_step(step)
        self._spawned_nodes.append(new_node)
        return CallHandle(new_node)
