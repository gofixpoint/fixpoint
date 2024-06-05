"""Simple implementation of a workflow"""

from uuid import uuid4
from typing import List, Optional

from pydantic import BaseModel, Field, PrivateAttr, computed_field

from .document import Document


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

    def goto_task(self, *, task_id: Optional[str], task_name: Optional[str]) -> None:
        """Transition to the given task.

        Specify one of either task_id or task_name.

        Tasks do not need to be declared ahead of time. When you go to a task,
        we infer its existence.
        """
        ...

    def goto_step(self, *, step_id: Optional[str], step_name: Optional[str]) -> None:
        """Transition to the given step.

        Specify one of either step_id or step_name.

        Steps do not need to be declared ahead of time. When you go to a step,
        we infer its existence.
        """
        ...

    def get_document(self, *, document_id: Optional[str], document_name: Optional[str]) -> Document:
        """Get a document from the cache.

        Specify one of either document_id or document_name. Gets the version of
        the document for the current workflow, task, and step.
        """
        ...
