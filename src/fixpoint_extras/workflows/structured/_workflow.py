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

import fixpoint
from fixpoint_extras.workflows.imperative import WorkflowRun, WorkflowContext
from .. import imperative
from .errors import DefinitionException
from ._helpers import validate_func_has_context_arg, Params, Ret


T = TypeVar("T")
C = TypeVar("C")


def run_workflow(
    workflow_defn: Type[C],
    args: Sequence[Any],
) -> None:
    fixpmeta: "WorkflowMetaFixp" = workflow_defn.__fixp_meta  # type: ignore[attr-defined]
    defn_instance = workflow_defn()
    # Double-underscore names get mangled to prevent conflicts
    fixp: "WorkflowInstanceFixp" = defn_instance._WorkflowMeta__fixp  # type: ignore[attr-defined]
    fixp.run(fixpmeta.ctx_factory)


class _WorkflowMeta(type):
    __fixp_meta: "WorkflowMetaFixp"
    __fixp: Optional["WorkflowInstanceFixp"] = None

    def __new__(
        cls: Type[C], name: str, bases: tuple[type, ...], attrs: Dict[str, Any]
    ) -> "C":
        attrs = dict(attrs)
        orig_init = attrs.get("__init__")

        def __init__(self: C, *args: Any, **kargs: Any) -> None:
            fixp_meta: WorkflowMetaFixp = attrs["__fixp_meta"]
            self.__fixp = WorkflowInstanceFixp(workflow_id=fixp_meta.workflow.id)  # type: ignore[attr-defined]
            if orig_init:
                orig_init(self, *args, **kargs)

        attrs["__fixp"] = None
        attrs["__init__"] = __init__

        if not _WorkflowMeta._has_entrypoint(attrs):
            raise DefinitionException(f"Workflow {name} has no entrypoint")

        retclass = super(_WorkflowMeta, cls).__new__(cls, name, bases, attrs)  # type: ignore[misc]
        return cast(C, retclass)

    @classmethod
    def _has_entrypoint(cls, attrs: Dict[str, Any]) -> bool:
        num_entrypoints = 0
        for v in attrs.values():
            if not callable(v):
                continue
            fixp = _get_workflow_entrypoint_fixp(v)
            if fixp:
                num_entrypoints += 1
        return num_entrypoints == 1


CtxFactory = Callable[[imperative.WorkflowRun], WorkflowContext]


class WorkflowMetaFixp:
    workflow: imperative.Workflow
    ctx_factory: CtxFactory

    def __init__(self, workflow_id: str, ctx_factory: CtxFactory) -> None:
        self.workflow = imperative.Workflow(id=workflow_id)
        self.ctx_factory = ctx_factory


class WorkflowInstanceFixp:
    workflow: imperative.Workflow
    ctx: Optional[WorkflowContext]
    workflow_run: Optional[imperative.WorkflowRun] = None

    def __init__(self, workflow_id: str) -> None:
        self.workflow = imperative.Workflow(id=workflow_id)

    def run(self, ctx_factory: CtxFactory) -> imperative.WorkflowContext:
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
    id: str, ctx_factory: CtxFactory = _default_ctx_factory
) -> Callable[[Type[C]], Type[C]]:
    def decorator(cls: Type[C]) -> Type[C]:
        cls.__fixp_meta = WorkflowMetaFixp(workflow_id=id, ctx_factory=ctx_factory)  # type: ignore[attr-defined]
        attrs = dict(cls.__dict__)
        return cast(Type[C], _WorkflowMeta(cls.__name__, cls.__bases__, attrs))

    return decorator


class WorkflowEntryFixp:
    pass


def workflow_entrypoint() -> Callable[[Callable[Params, Ret]], Callable[Params, Ret]]:
    def decorator(func: Callable[Params, Ret]) -> Callable[Params, Ret]:
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


def _get_workflow_entrypoint_fixp(
    fn: Callable[..., Any]
) -> Optional[WorkflowEntryFixp]:
    attr = getattr(fn, "__fixp", None)
    if isinstance(attr, WorkflowEntryFixp):
        return attr
    return None


def get_workflow_definition_meta_fixp(cls: Type[C]) -> Optional[WorkflowMetaFixp]:
    return getattr(cls, '__fixp_meta', None)


def get_workflow_instance_fixp(instance: C) -> Optional[WorkflowInstanceFixp]:
    return getattr(instance, '__fixp', None)
