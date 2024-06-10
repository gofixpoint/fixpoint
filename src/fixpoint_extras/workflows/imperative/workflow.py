"""Simple implementation of a workflow"""

from uuid import uuid4
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field, PrivateAttr, computed_field

from fixpoint.storage.protocol import SupportsStorage

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
    _documents: "_Documents" = PrivateAttr()
    _forms: "_Forms" = PrivateAttr()

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
        self._documents = _Documents(workflow_run=self)
        self._forms = _Forms(workflow_run=self)

    @property
    def documents(self) -> "_Documents":
        """Documents"""
        return self._documents

    @property
    def forms(self) -> "_Forms":
        """Forms"""
        return self._forms

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


# Class that wraps Form with WorkflowRun metadata
class FormWithMetadata(Form):
    """A form with workflow run metadata.

    This is a convenience class that wraps a form with workflow run metadata.
    """

    workflow_run_id: str


class _Forms:
    workflow_run: WorkflowRun
    _storage: Optional[SupportsStorage[FormWithMetadata]]
    _memory: Dict[str, FormWithMetadata]

    def __init__(
        self,
        workflow_run: WorkflowRun,
        storage: Optional[SupportsStorage[FormWithMetadata]] = None,
    ) -> None:
        self.workflow_run = workflow_run
        self._storage = storage
        self._memory = {}

    def get(self, *, form_id: str) -> Union[Form, None]:
        """Get a form from the cache.

        Gets the latest version of the form.
        """
        form = None
        if self._storage:
            # Form id is the primary identifier for a form, so specifying more fields is unecessary
            form_with_meta = self._storage.fetch(resource_id=form_id)
            form = Form(**form_with_meta.model_dump()) if form_with_meta else None
        else:
            # If we are not using a storage backend, we assume that the form is in memory
            form = self._memory.get(form_id, None)
        return form

    def store(
        self,
        *,
        schema: Type[BaseModel],
        # pylint: disable=redefined-builtin
        form_id: str,
        path: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Form:
        """Store a form in the cache.

        If a form with that id already exists in the workflow run, we will throw
        an error.

        The optional `path` is a "/" separate path of the form "/{task}/{step}".
        The "{step}" portion is optional. If you only specify the leading "/",
        it is stored at the root of the workflow run, outside of all tasks and
        steps. By default, we store the form at the current task and step.
        """
        form_with_meta = FormWithMetadata(
            schema=schema,
            id=form_id,
            path=path,
            metadata=metadata,
            workflow_run_id=self.workflow_run.id,
        )
        form_item = Form(**form_with_meta.model_dump())
        if self._storage:
            self._storage.insert(form_with_meta)
        else:
            self._memory[form_id] = form_with_meta
        return form_item

    def update(
        self,
        *,
        form_id: str,
        contents: Union[BaseModel, Dict[str, Any]],
    ) -> Form:
        """Update a form in the cache."""
        if isinstance(contents, BaseModel):
            form_with_meta = FormWithMetadata(
                id=form_id,
                workflow_run_id=self.workflow_run.id,
                **contents.model_dump(),
            )
        else:
            form_with_meta = FormWithMetadata(
                id=form_id, workflow_run_id=self.workflow_run.id, **contents
            )
        if self._storage:
            self._storage.update(form_with_meta)
        else:
            self._memory[form_id] = form_with_meta

        return Form(**form_with_meta.model_dump())

    def list(self, *, path: Optional[str] = None) -> List[Form]:
        """List all forms in the cache.

        The optional `path` is a "/" separate path of the form "/{task}/{step}".
        The "{step}" portion is optional. If you only specify the leading "/",
        we list all forms at the root of the workflow run, outside of all tasks
        and steps.
        """
        forms_with_meta: List[FormWithMetadata] = []
        forms: List[Form] = []
        conditions = {"workflow_run_id": self.workflow_run.id}
        if path:
            conditions["path"] = path
        if self._storage:
            forms_with_meta = self._storage.fetch_with_conditions(conditions=conditions)
            forms = [
                Form(**form_with_meta.model_dump())
                for form_with_meta in forms_with_meta
            ]
        else:
            # Filter forms in memory based on conditions
            forms = [
                Form(**form_with_meta.model_dump())
                for form_with_meta in self._memory.values()
                if all(
                    getattr(form_with_meta, key, None) == value
                    for key, value in conditions.items()
                )
            ]

        return forms
