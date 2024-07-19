"""Structured workflows: task definitions and task entrypoints

In a structured workflow, a task is a section of a workflow. Its state is
checkpointed, so if the task fails you can resume without losing computed work.
In a workflow, agents are able to recall memories, documents, and forms from
past or current tasks within the workflow.
"""

from functools import wraps
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    cast,
)

from ..constants import STEP_MAIN_ID
from .. import WorkflowStatus, imperative
from ..imperative import WorkflowRun
from ._context import WorkflowContext
from .errors import DefinitionException, InternalException
from ._callcache import CallCacheKind
from ._helpers import (
    validate_func_has_context_arg,
    AsyncFunc,
    Params,
    Ret,
    decorate_with_cache,
)


T = TypeVar("T")
C = TypeVar("C")


class _TaskMeta(type):
    __fixp_meta: "TaskMetaFixp"
    __fixp: Optional["TaskInstanceFixp"] = None

    def __new__(
        mcs: Type[C], name: str, bases: tuple[type, ...], attrs: Dict[str, Any]
    ) -> "C":
        attrs = dict(attrs)
        orig_init = attrs.get("__init__")

        def __init__(self: C, *args: Any, **kargs: Any) -> None:
            fixp_meta: TaskMetaFixp = attrs["__fixp_meta"]
            # pylint: disable=protected-access,unused-private-member
            self.__fixp = TaskInstanceFixp(task_id=fixp_meta.task_id)  # type: ignore[attr-defined]
            if orig_init:
                orig_init(self, *args, **kargs)

        attrs["__fixp"] = None
        attrs["__init__"] = __init__

        entry_fixp = _TaskMeta._get_entrypoint_fixp(attrs)
        if not entry_fixp:
            raise DefinitionException(f"Task {name} has no entrypoint")

        retclass = super(_TaskMeta, mcs).__new__(mcs, name, bases, attrs)  # type: ignore[misc]

        # Make sure that the entrypoint function has a reference to its
        # containing class. We do this because before a class instance is
        # created, class methods are unbound. This means that by default we
        # would not be able to get a reference to the class when provided the
        # entrypoint function.
        #
        # By adding this reference, when a function receives an arg like
        # `Task.entry` it can look up the class of `Task` and create an instance
        # of it.
        entry_fixp.task_cls = retclass

        return cast(C, retclass)

    @classmethod
    def _get_entrypoint_fixp(mcs, attrs: Dict[str, Any]) -> Optional["TaskEntryFixp"]:
        num_entrypoints = 0
        entrypoint_fixp = None
        for v in attrs.values():
            if not callable(v):
                continue
            fixp = get_task_entrypoint_fixp_from_fn(v)
            if fixp:
                entrypoint_fixp = fixp
                num_entrypoints += 1
        if num_entrypoints == 1:
            return entrypoint_fixp
        return None


class TaskMetaFixp:
    """Internal Fixpoint attributes for a task class definition"""

    task_id: str

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id


class TaskInstanceFixp:
    """Internal Fixpoint attributes for a task instance"""

    task_id: str
    workflow: Optional[imperative.Workflow]
    ctx: Optional[WorkflowContext]
    workflow_run: Optional[WorkflowRun] = None

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id

    def init_for_workflow(self, ctx: WorkflowContext) -> None:
        """Initialize the task instance for a workflow"""

        self.ctx = ctx
        self.workflow_run = ctx.workflow_run
        self.workflow = ctx.workflow_run.workflow


# pylint: disable=redefined-builtin
def task(id: str) -> Callable[[Type[C]], Type[C]]:
    """Decorate a class to mark it as a task definition

    A task definition is a class that represents a task in a workflow. The task
    class must have one method decorated with `structured.task_entrypoint()`.
    For example:

    ```
    @structured.task(id="my-task")
    class Task:
        @structured.task_entrypoint()
        def run(self, ctx: WorkflowContext, args: Dict[str, Any]) -> None:
            ...
    ```
    """

    def decorator(cls: Type[C]) -> Type[C]:
        # pylint: disable=protected-access
        cls.__fixp_meta = TaskMetaFixp(task_id=id)  # type: ignore[attr-defined]
        attrs = dict(cls.__dict__)
        return cast(Type[C], _TaskMeta(cls.__name__, cls.__bases__, attrs))

    return decorator


class TaskEntryFixp:
    """Internal Fixpoint attributes for a task entrypoint function"""

    task_cls: Optional[Type[Any]] = None


def task_entrypoint() -> Callable[[AsyncFunc[Params, Ret]], AsyncFunc[Params, Ret]]:
    """Mark the entrypoint function of a task class definition

    When you have a task class definition, you must have exactly one class
    method marked with `@task_entrypoint()`. This function is an instance
    method, and must accept at least a WorkflowContext argument as its first
    argument. You can have additional arguments beyond that.

    We recommend that you use one single extra argument, which should be
    JSON-serializable. This makes it easy to add and remove fields to that
    argument for backwards/forwards compatibilty.

    here is an example entrypoint definition inside a task class:

    ```
    @structured.task(id="my-task")
    class Task:
        @structured.task_entrypoint()
        def run(self, ctx: WorkflowContext, args: Dict[str, Any]) -> None:
            ...
    ```
    """

    def decorator(func: AsyncFunc[Params, Ret]) -> AsyncFunc[Params, Ret]:
        # pylint: disable=protected-access
        func.__fixp = TaskEntryFixp()  # type: ignore[attr-defined]

        validate_func_has_context_arg(func)

        @wraps(func)
        async def wrapper(*args: Params.args, **kwargs: Params.kwargs) -> Ret:
            taskentry_fixp = get_task_entrypoint_fixp_from_fn(func)
            if taskentry_fixp is None:
                raise InternalException("task entry __fixp is not defined")
            if taskentry_fixp.task_cls is None:
                raise InternalException("task entry __fixp.task_cls is not defined")
            task_meta_fixp = get_task_definition_meta_fixp(taskentry_fixp.task_cls)
            if task_meta_fixp is None:
                raise InternalException("task definition __fixp_meta is not defined")
            task_id = task_meta_fixp.task_id

            wrapped_func: AsyncFunc[Params, Ret] = decorate_with_cache(
                CallCacheKind.TASK, task_id
            )(func)
            result = await wrapped_func(*args, **kwargs)
            return result

        return wrapper

    return decorator


def get_task_entrypoint_from_defn(defn: Type[C]) -> Optional[Callable[..., Any]]:
    """Get the entrypoint function from a task class definition"""
    for attr in defn.__dict__.values():
        if callable(attr):
            fixp = get_task_entrypoint_fixp_from_fn(attr)
            if fixp:
                return cast(Callable[..., Any], attr)
    return None


def get_task_definition_meta_fixp(cls: Type[C]) -> Optional[TaskMetaFixp]:
    """Get the internal Fixpoint attributes from a task class definition"""
    attr = getattr(cls, "__fixp_meta", None)
    if isinstance(attr, TaskMetaFixp):
        return attr
    return None


def get_task_instance_fixp(instance: C) -> Optional[TaskInstanceFixp]:
    """Get the internal Fixpoint attributes from a task class instance"""
    # double-underscore names get mangled on class instances, so "__fixp"
    # becomes "_TaskMeta__fixp"
    attr = getattr(instance, "_TaskMeta__fixp", None)
    if isinstance(attr, TaskInstanceFixp):
        return attr
    return None


def get_task_entrypoint_fixp_from_fn(fn: Callable[..., Any]) -> Optional[TaskEntryFixp]:
    """Get the internal Fixpoint attributes from a task entrypoint function"""
    attr = getattr(fn, "__fixp", None)
    if isinstance(attr, TaskEntryFixp):
        return attr
    return None


async def call_task(
    ctx: WorkflowContext,
    task_entry: AsyncFunc[Params, Ret],
    args: Optional[List[Any]] = None,
    kwargs: Optional[Dict[str, Any]] = None,
) -> Ret:
    """Execute a task in a workflow.

    You must call `call_task` from within a structured workflow definition. ie
    from a class decorated with `@structured.workflow(...)`. A more complete example:

    ```
    @structured.task(id="my-task")
    class Task:
        @structured.task_entrypoint()
        def main(self, ctx: WorkflowContext, args: Dict[str, Any]) -> None:
            ...

    @structured.workflow(id="my-workflow")
    class MyWorkflow:
        @structured.workflow_entrypoint()
        def main(self, ctx: WorkflowContext, args: Dict[str, Any]) -> None:
            ####
            # this is the `call_task` invocation
            structured.call_task(ctx, Task.main, args[{"somevalue": "foobar"}])
    ```
    """
    entryfixp = get_task_entrypoint_fixp_from_fn(task_entry)
    if not entryfixp:
        raise DefinitionException(
            f'Task "{task_entry.__name__}" is not a valid task entrypoint'
        )

    task_defn = entryfixp.task_cls
    if not task_defn:
        raise DefinitionException(
            f'Task "{task_entry.__name__}" is not a valid task entrypoint'
        )
    fixpmeta = get_task_definition_meta_fixp(task_defn)
    if not fixpmeta:
        raise DefinitionException(
            f'Task "{task_defn.__name__}" is not a valid task definition'
        )

    task_instance = task_defn()
    # Double-underscore names get mangled to prevent conflicts
    instancefixp = get_task_instance_fixp(task_instance)
    if not instancefixp:
        raise DefinitionException(
            f'Task "{task_defn.__name__}" is not a valid task definition'
        )

    instancefixp.init_for_workflow(ctx)

    args = args or []
    kwargs = kwargs or {}
    task_handle = ctx.workflow_run.spawn_task(fixpmeta.task_id)
    new_ctx = ctx.clone(new_task=fixpmeta.task_id, new_step=STEP_MAIN_ID)
    # The Params type gets confused because we are injecting an additional
    # WorkflowContext. Ignore that error.
    try:
        res = await task_entry(task_instance, new_ctx, *args, **kwargs)  # type: ignore[arg-type]
    except:
        task_handle.close(WorkflowStatus.FAILED)
        raise
    else:
        task_handle.close(WorkflowStatus.COMPLETED)
    return res
