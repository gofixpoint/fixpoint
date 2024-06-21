from functools import wraps
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    ParamSpec,
    Sequence,
    Type,
    TypeVar,
    cast,
)

from fixpoint_extras.workflows.imperative import WorkflowRun, WorkflowContext
from .. import imperative
from .errors import DefinitionException
from ._helpers import validate_func_has_context_arg, Params, Ret


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
            self.__fixp = TaskInstanceFixp(task_id=fixp_meta.task_id)  # type: ignore[attr-defined]
            if orig_init:
                orig_init(self, *args, **kargs)

        attrs["__fixp"] = None
        attrs["__init__"] = __init__

        entry_fixp = _TaskMeta._get_entrypoint_fixp(attrs)
        if not entry_fixp:
            raise DefinitionException(f"Task {name} has no entrypoint")

        retclass = super(_TaskMeta, cls).__new__(cls, name, bases, attrs)  # type: ignore[misc]

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
    def _get_entrypoint_fixp(cls, attrs: Dict[str, Any]) -> Optional['TaskEntryFixp']:
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
    task_id: str

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id


class TaskInstanceFixp:
    task_id: str
    workflow: Optional[imperative.Workflow]
    ctx: Optional[WorkflowContext]
    workflow_run: Optional[WorkflowRun] = None

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id

    def init_workflow_run(self, ctx: WorkflowContext) -> None:
        self.ctx = ctx
        self.workflow_run = ctx.workflow_run
        self.workflow = ctx.workflow_run.workflow


def task(id: str) -> Callable[[Type[C]], Type[C]]:
    def decorator(cls: Type[C]) -> Type[C]:
        cls.__fixp_meta = TaskMetaFixp(task_id=id)  # type: ignore[attr-defined]
        attrs = dict(cls.__dict__)
        return cast(Type[C], _TaskMeta(cls.__name__, cls.__bases__, attrs))

    return decorator


class TaskEntryFixp:
    task_cls: Optional[Type[Any]] = None


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


def get_task_entrypoint_from_defn(defn: Type[C]) -> Optional[Callable[..., Any]]:
    for attr in defn.__dict__.values():
        if callable(attr):
            fixp = get_task_entrypoint_fixp_from_fn(attr)
            if fixp:
                return cast(Callable[..., Any], attr)
    return None


def get_task_definition_meta_fixp(cls: Type[C]) -> Optional[TaskMetaFixp]:
    attr = getattr(cls, "__fixp_meta", None)
    if isinstance(attr, TaskMetaFixp):
        return attr
    return None


def get_task_instance_fixp(instance: C) -> Optional[TaskInstanceFixp]:
    attr = getattr(instance, "__fixp", None)
    if isinstance(attr, TaskInstanceFixp):
        return attr
    return None


def get_task_entrypoint_fixp_from_fn(fn: Callable[..., Any]) -> Optional[TaskEntryFixp]:
    attr = getattr(fn, "__fixp", None)
    if isinstance(attr, TaskEntryFixp):
        return attr
    return None


async def call_task(
    ctx: WorkflowContext,
    task_entry: Callable[Params, Ret],
    args: Optional[List[Any]] = None,
    kwargs: Optional[Dict[str, Any]] = None,
) -> Ret:
    entryfixp = get_task_entrypoint_fixp_from_fn(task_entry)
    if not entryfixp:
        raise DefinitionException(
            f"Task \"{task_entry.__name__}\" is not a valid task entrypoint"
        )

    task_defn = entryfixp.task_cls
    if not task_defn:
        raise DefinitionException(
            f"Task \"{task_entry.__name__}\" is not a valid task entrypoint"
        )
    fixpmeta = get_task_definition_meta_fixp(task_defn)
    if not fixpmeta:
        raise DefinitionException(
            f"Task \"{task_defn.__name__}\" is not a valid task definition"
        )

    defn_instance = task_defn()
    # Double-underscore names get mangled to prevent conflicts
    fixp = get_task_instance_fixp(defn_instance)
    if not fixp:
        raise DefinitionException(
            f"Task \"{task_defn.__name__}\" is not a valid task definition"
        )

    fixp.init_workflow_run(ctx)

    args = args or []
    kwargs = kwargs or {}
    # The Params type gets confused because we are injecting an additional
    # WorkflowContext. Ignore that error.
    res = task_entry(ctx, *args, **kwargs)  # type: ignore[arg-type]
    return res
