from functools import wraps
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    ParamSpec,
    Sequence,
    Type,
    TypeVar,
    cast,
)

from fixpoint.workflow import SupportsWorkflowRun
from fixpoint_extras.workflows.imperative import WorkflowRun, WorkflowContext
from .. import imperative
from .errors import DefinitionException
from ._helpers import validate_func_has_context_arg


T = TypeVar("T")
C = TypeVar("C")


class _TaskMeta(type):
    __fixp_meta: "TaskMetaFixp"
    __fixp: Optional["TaskInstanceFixp"] = None

    def __new__(
        cls: Type[C], name: str, bases: tuple[type, ...], attrs: Dict[str, Any]
    ) -> "C":
        attrs = dict(attrs)
        orig_init = attrs.get("__init__")

        def __init__(self: C, *args: Any, **kargs: Any) -> None:
            fixp_meta: TaskMetaFixp = attrs["__fixp_meta"]
            self.__fixp = TaskInstanceFixp(workflow_id=fixp_meta.workflow.id)  # type: ignore[attr-defined]
            if orig_init:
                orig_init(self, *args, **kargs)

        attrs["__fixp"] = None
        attrs["__init__"] = __init__

        if not _TaskMeta._has_entrypoint(attrs):
            raise DefinitionException(f"Workflow {name} has no main task")

        retclass = super(_TaskMeta, cls).__new__(cls, name, bases, attrs)  # type: ignore[misc]
        return cast(C, retclass)

    @classmethod
    def _has_entrypoint(cls, attrs: Dict[str, Any]) -> bool:
        num_entrypoints = 0
        for v in attrs.values():
            if not callable(v):
                continue
            fixp = _get_task_entrypoint_fixp(v)
            if fixp:
                num_entrypoints += 1
        return num_entrypoints == 1


CtxFactory = Callable[[imperative.WorkflowRun], WorkflowContext]


class TaskMetaFixp:
    task_id: str

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id


class TaskInstanceFixp:
    workflow: imperative.Workflow
    ctx: Optional[WorkflowContext]
    # TODO(dbmikus) use imperative.WorkflowRun instead of SupportsWorkflowRun
    # workflow_run: Optional[imperative.WorkflowRun] = None
    workflow_run: Optional[SupportsWorkflowRun] = None

    def __init__(self, workflow_id: str) -> None:
        self.workflow = imperative.Workflow(id=workflow_id)

    def run(self, ctx: WorkflowContext) -> None:
        self.ctx = ctx
        self.workflow_run = ctx.workflow_run


def task(id: str) -> Callable[[Type[C]], Type[C]]:
    def decorator(cls: Type[C]) -> Type[C]:
        cls.__fixp_meta = TaskMetaFixp(task_id=id)  # type: ignore[attr-defined]
        attrs = dict(cls.__dict__)
        return cast(Type[C], _TaskMeta(cls.__name__, cls.__bases__, attrs))

    return decorator


class TaskEntryFixp:
    pass


Params = ParamSpec("Params")
Ret = TypeVar("Ret")


def task_entrypoint() -> Callable[[Callable[Params, Ret]], Callable[Params, Ret]]:
    def decorator(func: Callable[Params, Ret]) -> Callable[Params, Ret]:
        func.__fixp = TaskEntryFixp()  # type: ignore[attr-defined]

        validate_func_has_context_arg(func)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Ret:
            print("Before calling", func.__name__)
            result = func(*args, **kwargs)
            print("After calling", func.__name__)
            return result

        return cast(Callable[Params, Ret], wrapper)

    return decorator


def _get_task_entrypoint_fixp(
    fn: Callable[..., Any]
) -> Optional[TaskEntryFixp]:
    attr = getattr(fn, "__fixp", None)
    if isinstance(attr, TaskEntryFixp):
        return attr
    return None


def get_task_definition_meta_fixp(cls: Type[C]) -> Optional[TaskMetaFixp]:
    return getattr(cls, '__fixp_meta', None)


def get_task_instance_fixp(instance: C) -> Optional[TaskInstanceFixp]:
    return getattr(instance, '__fixp', None)
