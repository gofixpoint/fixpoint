from typing import Any, Callable, Optional, Sequence, Type, TypeVar, cast

from .. import imperative


T = TypeVar("T")
C = TypeVar("C")


def run_workflow(
    workflow_defn: Type[C],
    args: Sequence[Any],
) -> None:
    fixpmeta: "_FixpointMeta" = workflow_defn.__fixp_meta  # type: ignore[attr-defined]
    workflow_run = workflow_defn()
    # Double-underscore names get mangled to prevent conflicts
    fixp: "_FixpointInstance" = workflow_run._WorkflowMeta__fixp  # type: ignore[attr-defined]


class _WorkflowMeta(type):
    __fixp_meta: "_FixpointMeta"
    __fixp: Optional["_FixpointInstance"] = None

    def __new__(
        cls: Type[C], name: str, bases: tuple[type, ...], attrs: dict[str, Any]
    ) -> "C":
        attrs = dict(attrs)
        orig_init = attrs.get("__init__")

        def __init__(self: C, *args: Any, **kargs: Any) -> None:
            self.__fixp = _FixpointInstance(workflow_id=attrs["__fixp_meta"].workflow.id)  # type: ignore[attr-defined]
            if orig_init:
                orig_init(self, *args, **kargs)

        attrs["__fixp"] = None
        attrs["__init__"] = __init__

        retclass = super(_WorkflowMeta, cls).__new__(cls, name, bases, attrs)  # type: ignore[misc]
        return cast(C, retclass)


class _FixpointMeta:
    workflow: imperative.Workflow
    workflow_run: Optional[imperative.WorkflowRun] = None

    def __init__(self, workflow_id: str) -> None:
        self.workflow = imperative.Workflow(id=workflow_id)


class _FixpointInstance:
    workflow: imperative.Workflow
    workflow_run: Optional[imperative.WorkflowRun] = None

    def __init__(self, workflow_id: str) -> None:
        self.workflow = imperative.Workflow(id=workflow_id)

    def run(self) -> imperative.WorkflowRun:
        if self.workflow_run:
            return self.workflow_run
        run = self.workflow.run()
        self.workflow_run = run
        return run


def workflow(id: str) -> Callable[[Type[C]], Type[C]]:
    def decorator(cls: Type[C]) -> Type[C]:
        cls.__fixp_meta = _FixpointMeta(workflow_id=id)  # type: ignore[attr-defined]
        attrs = dict(cls.__dict__)
        return cast(Type[C], _WorkflowMeta(cls.__name__, cls.__bases__, attrs))

    return decorator
