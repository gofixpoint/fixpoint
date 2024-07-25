"""Simple implementation of a workflow"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Union, cast

from pydantic import (
    BaseModel,
    Field,
    PrivateAttr,
    computed_field,
    ConfigDict,
    SkipValidation,
)

from fixpoint._utils.ids import make_resource_uuid
from fixpoint.workflows.node_state import NodeState, CallHandle, SpawnGroup, NodeInfo
from fixpoint.workflows.human import HumanInTheLoop

from .document import Document
from .form import Form
from .config import StorageConfig, get_default_storage_config
from ._doc_storage import DocStorage
from ._form_storage import FormStorage

T = TypeVar("T", bound=BaseModel)


class Workflow(BaseModel):
    """A simple workflow implementation.

    From the Workflow, you can spawn Workflow Runs.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(description="The unique identifier for the workflow.")
    _memory: Dict[str, "WorkflowRun"] = PrivateAttr(default_factory=dict)

    def run(self, storage_config: Optional[StorageConfig] = None) -> "WorkflowRun":
        """Create and run a Workflow Run"""
        storage_config = storage_config or get_default_storage_config()
        new_workflow_run = WorkflowRun(
            workflow=self,
            storage_config=storage_config,
        )
        self._memory[new_workflow_run.id] = new_workflow_run
        return new_workflow_run

    def load_run(self, workflow_run_id: str) -> Union["WorkflowRun", None]:
        """Load a workflow run from memory."""
        # TODO(jakub): This should work with storage layers: postgres / supabase, in-memory
        # and on-disk
        return self._memory.get(workflow_run_id)


def new_workflow_run_id() -> str:
    """Create a new workflow run id"""
    return make_resource_uuid("wfrun")


class WorkflowRun(BaseModel):
    """A workflow run.

    The workflow run has a cache for objects, such as documents, forms, and
    ChatCompletions.

    It also has memory to recall previous workflow steps, tasks, and LLM
    inferences.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    _id: str = PrivateAttr(default_factory=new_workflow_run_id)
    _task_ids: List[str] = PrivateAttr(default_factory=list)

    workflow: Workflow
    _documents: "_Documents" = PrivateAttr()
    _forms: "_Forms" = PrivateAttr()

    storage_config: SkipValidation[Optional[StorageConfig]] = Field(
        exclude=True, default=None
    )

    _node_state: NodeState = PrivateAttr(default_factory=NodeState)
    _human_in_the_loop: HumanInTheLoop = PrivateAttr()
    state: dict[str, Any] = Field(
        description="State of the workflow run", default_factory=dict
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
        docs_storage: Optional[DocStorage] = None
        forms_storage: Optional[FormStorage] = None
        if self.storage_config:
            if self.storage_config.docs_storage:
                docs_storage = self.storage_config.docs_storage
            if self.storage_config.forms_storage:
                forms_storage = self.storage_config.forms_storage
        self._documents = _Documents(workflow_run=self, storage=docs_storage)
        self._forms = _Forms(workflow_run=self, storage=forms_storage)
        self._human_in_the_loop = HumanInTheLoop(
            workflow_id=self.workflow_id,
            workflow_run_id=self.id,
        )

    @property
    def docs(self) -> "_Documents":
        """Documents"""
        return self._documents

    @property
    def documents(self) -> "_Documents":
        """Documents"""
        return self._documents

    @property
    def forms(self) -> "_Forms":
        """Forms"""
        return self._forms

    @property
    def node_info(self) -> NodeInfo:
        """The info about the current execution node

        What task or step are we in, and what is it's status?
        """
        return self._node_state.info

    @property
    def human(self) -> HumanInTheLoop:
        """Get the human in the loop for the workflow run"""
        return self._human_in_the_loop

    # pylint: disable=unused-argument
    def goto_task(self, task_id: str) -> None:
        """Transition to the given task.

        Tasks do not need to be declared ahead of time. When you go to a task,
        we infer its existence.
        """
        self._node_state = self._node_state.add_task(task_id)

    # pylint: disable=unused-argument
    def goto_step(self, step_id: str, task_id: Optional[str] = None) -> None:
        """Transition to the given step.

        Steps do not need to be declared ahead of time. When you go to a step,
        we infer its existence.
        """
        self._node_state = self._node_state.add_step(step_id, task_id)

    def _update_node_state(self, new_state: NodeState) -> NodeState:
        self._node_state = new_state
        return self._node_state

    def call_step(self, step_id: str) -> CallHandle:
        """Call a step"""
        self._node_state = self._node_state.add_step(step_id)
        return CallHandle(self._node_state, self._update_node_state)

    def call_task(self, task_id: str) -> CallHandle:
        """Call a task"""
        self._node_state = self._node_state.add_task(task_id)
        return CallHandle(self._node_state, self._update_node_state)

    def spawn_step(self, step_id: str) -> CallHandle:
        """Spawn a step"""
        new_node = self._node_state.add_step(step_id)
        return CallHandle(new_node)

    def spawn_task(self, task_id: str) -> CallHandle:
        """Spawn a task"""
        new_node = self._node_state.add_task(task_id)
        return CallHandle(new_node)

    def spawn_group(self) -> SpawnGroup:  # pylint: disable=invalid-name
        """Handle for spawning a group of tasks"""
        return SpawnGroup(node_state=self._node_state)

    def clone(
        self, new_task: str | None = None, new_step: str | None = None
    ) -> "WorkflowRun":
        """Clones the workflow run"""
        # we cannot deep copy because some of the fields cannot be pickled,
        # which is what the pydantic copy method uses
        new_self = self.model_copy(deep=False)
        # pylint: disable=protected-access
        new_self._node_state = self._node_state.model_copy(deep=False)
        new_self._node_state.info = self._node_state.info.model_copy(deep=True)
        if new_task:
            new_self._node_state.info.task = new_task
        if new_step:
            new_self._node_state.info.step = new_step
        return new_self


class _Documents:
    workflow_run: WorkflowRun
    _storage: Optional[DocStorage]
    _memory: Dict[str, Document]

    def __init__(
        self,
        workflow_run: WorkflowRun,
        storage: Optional[DocStorage] = None,
    ) -> None:
        self.workflow_run = workflow_run
        self._storage = storage
        self._memory: Dict[str, Document] = {}

    def get(
        self,
        document_id: str,
    ) -> Union[Document, None]:
        """Get a document from the cache.

        Gets the latest version of the document.
        """
        document = None
        if self._storage:
            document = self._storage.get(document_id)
        else:
            document = self._memory.get(document_id, None)
        return document

    def store(
        self,
        *,
        id: str,
        contents: str,
        metadata: Optional[dict[str, Any]] = None,
        # pylint: disable=redefined-builtin
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
        if path is None:
            path = self.workflow_run.node_info.id
        document = Document(
            id=id,
            workflow_id=self.workflow_run.workflow_id,
            workflow_run_id=self.workflow_run.id,
            path=path,
            contents=contents,
            metadata=metadata or {},
        )
        if self._storage:
            self._storage.create(document)
        else:
            self._memory[id] = document
        return document

    def update(
        self,
        *,
        document_id: str,
        contents: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Document:
        """Update a document in the cache."""
        if self._storage:
            document = self.get(document_id=document_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")
            document.contents = contents
            if metadata:
                document.metadata = metadata

        else:
            # copy it so the document object is immutable
            document = self._memory[document_id].model_copy()
            if metadata is not None:
                document.metadata = metadata
            document.contents = contents

        if self._storage:
            self._storage.update(document)
        else:
            self._memory[document_id] = document

        return document

    def list(self, *, path: Optional[str] = None) -> List[Document]:
        """List all documents in the cache.

        The optional `path` is a "/" separate path of the form "/{task}/{step}".
        The "{step}" portion is optional. If you only specify the leading "/",
        we list all documents at the root of the workflow, outside of all tasks and
        steps.
        """

        if self._storage:
            documents = self._storage.list(
                path=path, workflow_run_id=self.workflow_run.id
            )
        else:
            conditions = {"workflow_run_id": self.workflow_run.id}
            if path:
                conditions["path"] = path
            documents = [
                doc
                for doc in self._memory.values()
                if all(
                    getattr(doc, key, None) == value
                    for key, value in conditions.items()
                )
            ]
        return documents


class _Forms:
    workflow_run: WorkflowRun
    _storage: Optional[FormStorage]
    _memory: Dict[str, Form[BaseModel]]

    def __init__(
        self,
        workflow_run: WorkflowRun,
        storage: Optional[FormStorage] = None,
    ) -> None:
        self.workflow_run = workflow_run
        self._storage = storage
        self._memory: Dict[str, Form[BaseModel]] = {}

    def get(self, form_id: str) -> Union[Form[BaseModel], None]:
        """Get a form from the cache.

        Gets the latest version of the form.
        """
        form = None
        if self._storage:
            # Form id is the primary identifier for a form, so specifying more fields is unecessary
            form = self._storage.get(form_id)
        else:
            # If we are not using a storage backend, we assume that the form is in memory
            form = self._memory.get(form_id, None)
        return form

    def store(
        self,
        *,
        schema: Type[T],
        # pylint: disable=redefined-builtin
        form_id: str,
        path: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Form[T]:
        """Store a form in the workflow run.

        If a form with that id already exists in the workflow run, we will throw
        an error.

        The optional `path` is a "/" separate path of the form "/{task}/{step}".
        The "{step}" portion is optional. If you only specify the leading "/",
        it is stored at the root of the workflow run, outside of all tasks and
        steps. By default, we store the form at the current task and step.
        """
        # TODO(jakub): Pass in contents as well
        if path is None:
            path = self.workflow_run.node_info.id
        form = Form[T](
            form_schema=schema,
            id=form_id,
            workflow_id=self.workflow_run.workflow_id,
            workflow_run_id=self.workflow_run.id,
            path=path,
            metadata=metadata or {},
        )
        if self._storage:
            # Storage layer only expects "BaseModel"
            self._storage.create(cast(Form[BaseModel], form))
        else:
            self._memory[form_id] = cast(Form[BaseModel], form)

        return form

    def update(
        self,
        *,
        form_id: str,
        contents: Union[T, Dict[str, Any]],
        metadata: Optional[dict[str, Any]] = None,
    ) -> Form[T]:
        """Update a form in the workflow run.

        Updates a form, setting the specified fields. If a field is not preset,
        it is not set. To set a field to None, specify it.
        """

        if self._storage:
            # This should mirror BaseModel model_copy, but work with storage
            form = self.get(form_id=form_id)
            if not form:
                raise ValueError(f"Form {form_id} not found")
            form.update_contents(contents)
            if metadata:
                form.metadata = metadata

        else:
            # copy it so the document object is immutable
            form = self._memory[form_id].model_copy()
            if metadata is not None:
                form.metadata = metadata
            form.update_contents(contents)

        if self._storage:
            self._storage.update(form)
        else:
            self._memory[form_id] = form

        return cast(Form[T], form)

    def list(self, *, path: Optional[str] = None) -> List[Form[BaseModel]]:
        """List all forms in the cache.

        The optional `path` is a "/" separate path of the form "/{task}/{step}".
        The "{step}" portion is optional. If you only specify the leading "/",
        we list all forms at the root of the workflow run, outside of all tasks
        and steps.
        """
        forms_with_meta: List[Form[BaseModel]] = []
        forms: List[Form[BaseModel]] = []
        if self._storage:
            forms_with_meta = self._storage.list(
                path=path, workflow_run_id=self.workflow_run.id
            )
            forms = [
                Form(**form_with_meta.model_dump())
                for form_with_meta in forms_with_meta
            ]
        else:
            conditions = {"workflow_run_id": self.workflow_run.id}
            if path:
                conditions["path"] = path
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
