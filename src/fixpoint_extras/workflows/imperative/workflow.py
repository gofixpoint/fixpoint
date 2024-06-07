"""Simple implementation of a workflow"""

from uuid import uuid4
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field, PrivateAttr, computed_field

from .document import Document
from .form import Form


class NodeState(BaseModel):
    """
    Each task or step in a workflow run is a "node". This keeps track of which
    node the workflow run is in.
    """

    task: str = Field(description="The task that the node is in")
    step: str = Field(description="The step that the node is in")

    @computed_field  # type: ignore[misc]
    @property
    def id(self) -> str:
        """The node's identifier within the workflow run"""
        return f"/{self.task}/{self.step}"


class Workflow(BaseModel):
    """A simple workflow implementation.

    From the Workflow, you can spawn Workflow Runs.
    """

    id: str = Field(description="The unique identifier for the workflow.")

    def run(self) -> "WorkflowRun":
        """Create and run a Workflow Run"""
        return WorkflowRun(workflow=self)


class WorkflowRun(BaseModel):
    """A workflow run.

    The workflow run has a cache for objects, such as documents, forms, and
    ChatCompletions.

    It also has memory to recall previous workflow steps, tasks, and LLM
    inferences.
    """

    _id: str = PrivateAttr(default_factory=lambda: str(uuid4()))
    _task_ids: List[str] = PrivateAttr(default_factory=list)

    workflow: Workflow
    documents: "_Documents" = PrivateAttr()
    forms: "_Forms" = PrivateAttr()

    node_state: NodeState = Field(
        default_factory=lambda: NodeState(task="__start__", step="__start__")
    )

    @computed_field  # type: ignore[misc]
    @property
    def workflow_id(self) -> str:
        """The ID of the Workflow we are running"""
        return self.workflow.id

    @computed_field  # type: ignore[misc]
    @property
    def id(self) -> str:
        """The workflow run's unique identifier"""
        return self._id

    def model_post_init(self, _context: Any) -> None:
        self.documents = _Documents(workflow_run=self)
        self.forms = _Forms(workflow_run=self)

    # pylint: disable=unused-argument
    def goto_task(self, *, task_id: str) -> None:
        """Transition to the given task.

        Tasks do not need to be declared ahead of time. When you go to a task,
        we infer its existence.
        """
        raise NotImplementedError()

    # pylint: disable=unused-argument
    def goto_step(self, *, step_id: str) -> None:
        """Transition to the given step.

        Steps do not need to be declared ahead of time. When you go to a step,
        we infer its existence.
        """
        raise NotImplementedError()


class _Documents:
    workflow_run: WorkflowRun

    def __init__(self, workflow_run: WorkflowRun) -> None:
        self.workflow_run = workflow_run

    def get(
        self,
        *,
        document_id: Optional[str],
    ) -> Document:
        """Get a document from the cache.

        Gets the latest version of the document.
        """
        raise NotImplementedError()

    def store(
        self,
        *,
        contents: Union[BaseModel, Dict[str, Any]],
        # pylint: disable=redefined-builtin
        id: Optional[str] = None,
        path: Optional[str] = None,
    ) -> Document:
        """Store a document in the cache.

        If a document with that id already exists in the workflow, we will throw an
        error.

        The optional `path` is a "/" separate path of the form "/{task}/{step}".
        The "{step}" portion is optional. If you only specify the leading "/",
        it is stored at the root of the workflow, outside of all tasks and
        steps. By default, we store the document at the current task and step.
        """
        raise NotImplementedError()

    def update(
        self,
        *,
        document_id: Optional[str],
        contents: Union[BaseModel, Dict[str, Any]],
    ) -> Document:
        """Update a document in the cache."""
        raise NotImplementedError()

    def list(self, *, path: Optional[str] = None) -> List[Document]:
        """List all documents in the cache.

        The optional `path` is a "/" separate path of the form "/{task}/{step}".
        The "{step}" portion is optional. If you only specify the leading "/",
        we list all documents at the root of the workflow, outside of all tasks and
        steps.
        """
        raise NotImplementedError()


class _Forms:
    workflow_run: WorkflowRun

    def __init__(self, workflow_run: WorkflowRun) -> None:
        self.workflow_run = workflow_run

    def get(self, *, form_id: Optional[str]) -> Form:
        """Get a form from the cache.

        Gets the latest version of the form.
        """
        raise NotImplementedError()

    def store(
        self,
        *,
        schema: Type[BaseModel],
        # pylint: disable=redefined-builtin
        id: Optional[str] = None,
        path: Optional[str] = None,
    ) -> Form:
        """Store a form in the cache.

        If a form with that id already exists in the workflow run, we will throw
        an error.

        The optional `path` is a "/" separate path of the form "/{task}/{step}".
        The "{step}" portion is optional. If you only specify the leading "/",
        it is stored at the root of the workflow run, outside of all tasks and
        steps. By default, we store the form at the current task and step.
        """
        raise NotImplementedError()

    def update(
        self,
        *,
        form_id: Optional[str],
        contents: Union[BaseModel, Dict[str, Any]],
    ) -> Form:
        """Update a form in the cache."""
        raise NotImplementedError()

    def list(self, *, path: Optional[str] = None) -> List[Form]:
        """List all forms in the cache.

        The optional `path` is a "/" separate path of the form "/{task}/{step}".
        The "{step}" portion is optional. If you only specify the leading "/",
        we list all forms at the root of the workflow run, outside of all tasks
        and steps.
        """
        raise NotImplementedError()
