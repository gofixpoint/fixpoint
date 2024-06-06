"""Simple implementation of a workflow"""

from uuid import uuid4
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, PrivateAttr, computed_field

from .document import Document


class NodeState(BaseModel):
    """
    Each task or step in a workflow is a "node". This keeps track of which node
    the workflow is in.
    """

    task: str = Field(description="The task that the node is in")
    step: str = Field(description="The step that the node is in")

    @computed_field  # type: ignore[misc]
    @property
    def id(self) -> str:
        """The workflow's unique identifier"""
        return f"/{self.task}/{self.step}"


class Workflow(BaseModel):
    """A simple workflow implementation

    The workflow has a cache for objects, such as documents, forms, and
    ChatCompletions.

    It also has memory to recall previous workflow steps, tasks, and LLM
    inferences.
    """

    _id: str = PrivateAttr(default_factory=lambda: str(uuid4()))
    _run_id: str = PrivateAttr(default_factory=lambda: str(uuid4()))
    _task_ids: List[str] = PrivateAttr(default_factory=list)

    node_state: NodeState = Field(default_factory=lambda: NodeState(task="__start__", step="__start__"))

    name: Optional[str] = Field(
        default=None,
        description=(
            "An optional name for the workflow. Must be unique within the workspace."
            " Think of it like a filename."
        ),
    )

    @computed_field  # type: ignore[misc]
    @property
    def id(self) -> str:
        """The workflow's unique identifier"""
        return self._id

    @computed_field  # type: ignore[misc]
    @property
    def run_id(self) -> str:
        """The workflow's unique identifier"""
        return self._run_id

    def goto_task(self, *, task_name: str) -> None:
        """Transition to the given task.

        Tasks do not need to be declared ahead of time. When you go to a task,
        we infer its existence.
        """
        ...

    def goto_step(self, *, step_name: str) -> None:
        """Transition to the given step.

        Specify one of either step_id or step_name.

        Steps do not need to be declared ahead of time. When you go to a step,
        we infer its existence.
        """
        ...

    def get_document(self, *, document_id: Optional[str], document_name: Optional[str]) -> Document:
        """Get a document from the cache.

        Specify one of either document_id or document_name. Gets the latest
        version of the document for the current workflow, task, and step.
        """
        raise NotImplementedError()

    def store_document(self, *, contents: Union[BaseModel, Dict[str, Any]], name: Optional[str] = None, path: Optional[str] = None) -> Document:
        """Store a document in the cache.

        If name is provided, the document will be stored under that name. If a
        document with that name already exists in the workflow, we will throw an
        error.

        The optional `path` is a "/" separate path of the form "/{task}/{step}".
        The "{step}" portion is optional. If you only specify the leading "/",
        it is stored at the root of the workflow, outside of all tasks and
        steps. By default, we store the document at the current task and step.
        """
        raise NotImplementedError()

    def update_document(self, *, document_id: Optional[str], document_name: Optional[str], contents: Union[BaseModel, Dict[str, Any]]) -> Document:
        """Update a document in the cache.

        Specify one of either document_id or document_name.
        """
        raise NotImplementedError()
