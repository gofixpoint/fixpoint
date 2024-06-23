"""Structured workflows: workflow definitions and workflow entrypoints

In a structured workflow, a workflow is the highest level of the structured
workflow program. It can call other tasks and steps. Within the workflow's tasks
and steps, we checkpoint progress so if any part fails we can resume without
losing computed work or spending extra on LLM inference.

In a workflow, agents are able to recall memories, documents, and forms from
past or current tasks within the workflow.
"""

from functools import wraps
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    Sequence,
    Type,
    TypeVar,
    cast,
)

import fixpoint
from fixpoint_extras.workflows.imperative import WorkflowRun, WorkflowContext
from .. import imperative
from .errors import DefinitionException
from ._helpers import validate_func_has_context_arg, Params, Ret


T = TypeVar("T")
C = TypeVar("C")


class _WorkflowMeta(type):
    __fixp_meta: "WorkflowMetaFixp"
    __fixp: Optional["WorkflowInstanceFixp"] = None

    def __new__(
        mcs: Type[C], name: str, bases: tuple[type, ...], attrs: Dict[str, Any]
    ) -> "C":
        attrs = dict(attrs)
        orig_init = attrs.get("__init__")

        def __init__(self: C, *args: Any, **kargs: Any) -> None:
            fixp_meta: WorkflowMetaFixp = attrs["__fixp_meta"]
            # pylint: disable=unused-private-member,protected-access
            self.__fixp = WorkflowInstanceFixp(  # type: ignore[attr-defined]
                workflow_id=fixp_meta.workflow.id
            )
            if orig_init:
                orig_init(self, *args, **kargs)

        attrs["__fixp"] = None
        attrs["__init__"] = __init__

        entrypoint_fixp = _WorkflowMeta._get_entrypoint_fixp(attrs)
        if not entrypoint_fixp:
            raise DefinitionException(f"Workflow {name} has no entrypoint")

        retclass = super(_WorkflowMeta, mcs).__new__(mcs, name, bases, attrs)  # type: ignore[misc]

        # Make sure that the entrypoint function has a reference to its
        # containing class. We do this because before a class instance is
        # created, class methods are unbound. This means that by default we
        # would not be able to get a reference to the class when provided the
        # entrypoint function.
        #
        # By adding this reference, when a function receives an arg like `Workflow.entry`
        # it can look up the class of `Workflow` and create an instance of it.
        entrypoint_fixp.workflow_cls = retclass

        return cast(C, retclass)

    @classmethod
    def _get_entrypoint_fixp(
        mcs, attrs: Dict[str, Any]
    ) -> Optional["WorkflowEntryFixp"]:
        num_entrypoints = 0
        entrypoint_fixp = None
        for v in attrs.values():
            if not callable(v):
                continue
            fixp = get_workflow_entrypoint_fixp(v)
            if fixp:
                entrypoint_fixp = fixp
                num_entrypoints += 1
        if num_entrypoints == 1:
            return entrypoint_fixp
        return None


CtxFactory = Callable[[imperative.WorkflowRun], WorkflowContext]


class WorkflowMetaFixp:
    """Internal fixpoint attribute for a workflow class definition."""

    workflow: imperative.Workflow
    ctx_factory: CtxFactory

    def __init__(self, workflow_id: str, ctx_factory: CtxFactory) -> None:
        self.workflow = imperative.Workflow(id=workflow_id)
        self.ctx_factory = ctx_factory


class WorkflowInstanceFixp:
    """Internal fixpoint attribute for a workflow instance."""

    workflow: imperative.Workflow
    ctx: Optional[WorkflowContext]
    workflow_run: Optional[imperative.WorkflowRun] = None

    def __init__(self, workflow_id: str) -> None:
        self.workflow = imperative.Workflow(id=workflow_id)
        self.ctx = None
        self.workflow_run = None

    def run(self, ctx_factory: CtxFactory) -> imperative.WorkflowContext:
        """Internal function to "run" a workflow.

        Create a workflow object instance and context. It doesn't actually call
        the workflow entrypoint, but it initializes the Fixpoint workflow
        instance attribute with a workflow run and a workflow context.
        """

        if self.ctx:
            return self.ctx
        run = self.workflow.run()
        self.workflow_run = run
        ctx = ctx_factory(run)
        self.ctx = ctx
        return ctx


def _default_ctx_factory(run: WorkflowRun) -> WorkflowContext:
    return WorkflowContext.from_workflow(
        workflow_run=run,
        agents={},
        memory=fixpoint.memory.Memory(),
        # TODO(dbmikus) change default to an in-memory cache
        cache=fixpoint.cache.ChatCompletionDiskTLRUCache.from_tmpdir(
            # 1 hour
            ttl_s=60 * 60,
            # 100 MB
            size_limit_bytes=1024 * 1024 * 100,
        ),
    )


def workflow(
    id: str,  # pylint: disable=redefined-builtin
    ctx_factory: CtxFactory = _default_ctx_factory,
) -> Callable[[Type[C]], Type[C]]:
    """Decorate a class to mark it as a workflow definition

    A workflow definition is a class that represents a workflow. The workflow
    class must have one method decorated with `structured.workflow_entrypoint()`.
    For example:

    ```
    @structured.workflow(id="my-workflow")
    class Workflow:
        @structured.workflow_entrypoint()
        def run(self, ctx: WorkflowContext, args: Dict[str, Any]) -> None:
            ...
    ```
    """

    def decorator(cls: Type[C]) -> Type[C]:
        # pylint: disable=protected-access
        cls.__fixp_meta = WorkflowMetaFixp(  # type: ignore[attr-defined]
            workflow_id=id, ctx_factory=ctx_factory
        )
        attrs = dict(cls.__dict__)
        return cast(Type[C], _WorkflowMeta(cls.__name__, cls.__bases__, attrs))

    return decorator


class WorkflowEntryFixp:
    """Internal fixpoint attribute for a workflow entrypoint."""

    workflow_cls: Optional[Type[Any]] = None


def workflow_entrypoint() -> Callable[[Callable[Params, Ret]], Callable[Params, Ret]]:
    """Mark the entrypoint function of a workflow class definition

    When you have a workflow class definition, you must have exactly one class
    method marked with `@workflow_entrypoint()`. This function is an instance
    method, and must accept at least a WorkflowContext argument as its first
    argument. You can have additional arguments beyond that.

    We recommend that you use one single extra argument, which should be
    JSON-serializable. This makes it easy to add and remove fields to that
    argument for backwards/forwards compatibilty.

    here is an example entrypoint definition inside a workflow class:

    ```
    @structured.workflow(id="my-workflow")
    class Workflow:
        @structured.workflow_entrypoint()
        def run(self, ctx: WorkflowContext, args: Dict[str, Any]) -> None:
            ...
    ```
    """

    def decorator(func: Callable[Params, Ret]) -> Callable[Params, Ret]:
        # pylint: disable=protected-access
        func.__fixp = WorkflowEntryFixp()  # type: ignore[attr-defined]

        validate_func_has_context_arg(func)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Ret:
            print("Before calling", func.__name__)
            result = func(*args, **kwargs)
            print("After calling", func.__name__)
            return result

        return cast(Callable[Params, Ret], wrapper)

    return decorator


def get_workflow_entrypoint_fixp(fn: Callable[..., Any]) -> Optional[WorkflowEntryFixp]:
    """Get the internal fixpoint attribute for a workflow entrypoint.

    Must be called on the entrypoint function.
    """
    attr = getattr(fn, "__fixp", None)
    if isinstance(attr, WorkflowEntryFixp):
        return attr
    return None


def get_workflow_definition_meta_fixp(cls: Type[C]) -> Optional[WorkflowMetaFixp]:
    """Get the internal fixpoint attribute for a workflow definition."""
    attr = getattr(cls, "__fixp_meta", None)
    if not isinstance(attr, WorkflowMetaFixp):
        return None
    return attr


def get_workflow_instance_fixp(instance: C) -> Optional[WorkflowInstanceFixp]:
    """Get the internal fixpoint attribute for a workflow instance."""
    # double-underscore names get mangled on class instances, so "__fixp"
    # becomes "_WorkflowMeta__fixp"
    attr = getattr(instance, "_WorkflowMeta__fixp", None)
    if not isinstance(attr, WorkflowInstanceFixp):
        return None
    return attr


def run_workflow(
    workflow_entry: Callable[Params, Ret],
    args: Optional[Sequence[Any]] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    ctx_factory: Optional[CtxFactory] = None,
) -> Ret:
    """Runs a structured workflow.

    You must call `call_task` from within a structured workflow definition. ie
    from a class decorated with `@structured.workflow(...)`. A more complete example:

    ```
    @structured.workflow(id="my-workflow")
    class MyWorkflow:
        @structured.workflow_entrypoint()
        def main(self, ctx: WorkflowContext, args: Dict[str, Any]) -> None:
            ...


    structured.run_workflow(MyWorkflow.main, args=[{"somevalue": "foobar"}])
    ```

    If you pass in a `ctx_factory`, it will be used instead of the `ctx_factory`
    defined on the workflow class.
    """
    entryfixp = get_workflow_entrypoint_fixp(workflow_entry)
    if not entryfixp:
        raise DefinitionException(
            f'Workflow "{workflow_entry.__name__}" is not a valid workflow entrypoint'
        )
    if not entryfixp.workflow_cls:
        raise DefinitionException(
            f'Workflow "{workflow_entry.__name__}" is not inside a decorated workflow class'
        )
    workflow_defn = entryfixp.workflow_cls

    fixpmeta = get_workflow_definition_meta_fixp(workflow_defn)
    if not isinstance(fixpmeta, WorkflowMetaFixp):
        raise DefinitionException(
            f'Workflow "{workflow_defn.__name__}" is not a valid workflow definition'
        )
    workflow_instance = workflow_defn()
    fixp = get_workflow_instance_fixp(workflow_instance)
    if not fixp:
        raise DefinitionException(
            f'Workflow "{workflow_defn.__name__}" is not a valid workflow instance'
        )
    fixp.run(ctx_factory or fixpmeta.ctx_factory)

    if not fixp.ctx:
        # this is an internal error, not a user error
        raise ValueError("workflow run context is None")

    args = args or []
    kwargs = kwargs or {}
    # The Params type gets confused because we are injecting an additional
    # WorkflowContext. Ignore that error.
    res = workflow_entry(workflow_instance, fixp.ctx, *args, **kwargs)  # type: ignore[arg-type]
    return res
