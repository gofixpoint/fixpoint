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

        entrypoint_fixp = _WorkflowMeta._get_entrypoint_fixp(attrs)
        if not entrypoint_fixp:
            raise DefinitionException(f"Workflow {name} has no entrypoint")

        retclass = super(_WorkflowMeta, cls).__new__(cls, name, bases, attrs)  # type: ignore[misc]

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
    def _get_entrypoint_fixp(cls, attrs: Dict[str, Any]) -> Optional['WorkflowEntryFixp']:
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
        self.ctx = None
        self.workflow_run = None

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
    workflow_cls: Optional[Type[Any]] = None


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


def get_workflow_entrypoint_fixp(
    fn: Callable[..., Any]
) -> Optional[WorkflowEntryFixp]:
    attr = getattr(fn, "__fixp", None)
    if isinstance(attr, WorkflowEntryFixp):
        return attr
    return None


def get_workflow_definition_meta_fixp(cls: Type[C]) -> Optional[WorkflowMetaFixp]:
    attr = getattr(cls, "__fixp_meta", None)
    if not isinstance(attr, WorkflowMetaFixp):
        return None
    return attr


def get_workflow_instance_fixp(instance: C) -> Optional[WorkflowInstanceFixp]:
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
) -> Ret:
    entryfixp = get_workflow_entrypoint_fixp(workflow_entry)
    if not entryfixp:
        raise DefinitionException(f"Workflow \"{workflow_entry.__name__}\" is not a valid workflow entrypoint")
    if not entryfixp.workflow_cls:
        raise DefinitionException(f"Workflow \"{workflow_entry.__name__}\" is not inside a decorated workflow class")
    workflow_defn = entryfixp.workflow_cls

    fixpmeta = get_workflow_definition_meta_fixp(workflow_defn)
    if not isinstance(fixpmeta, WorkflowMetaFixp):
        raise DefinitionException(
            f"Workflow \"{workflow_defn.__name__}\" is not a valid workflow definition"
        )
    workflow_instance = workflow_defn()
    fixp = get_workflow_instance_fixp(workflow_instance)
    if not fixp:
        raise DefinitionException(
            f"Workflow \"{workflow_defn.__name__}\" is not a valid workflow instance"
        )
    fixp.run(fixpmeta.ctx_factory)

    if not fixp.ctx:
        # this is an internal error, not a user error
        raise ValueError("workflow run context is None")

    args = args or []
    kwargs = kwargs or {}
    # The Params type gets confused because we are injecting an additional
    # WorkflowContext. Ignore that error.
    res = workflow_entry(workflow_instance, fixp.ctx, *args, **kwargs) # type: ignore[arg-type]
    return res
