from typing import Any, Callable, Optional, Sequence, Type, TypeVar, cast

from .. import imperative


T = TypeVar('T')

def run_workflow(
        workflow_task: Callable[[imperative.WorkflowContext, Any], Any],
        args: Sequence[Any],
    ) -> None:
    workflow = workflow_task
    print("DBM running")
    print("Workflow ID:", workflow_task.__fixp_meta.workflow.id)
    workflow = workflow_task()
    print("Workflow run before:", workflow.__fixp)

C = TypeVar('C')

class _WorkflowMeta(type):
    __fixp_meta: "_FixpointMeta"
    __fixp: Optional['_FixpointInstance'] = None

    def __new__(cls: Type[C], fixp_meta: '_FixpointMeta', name: str, bases: tuple[type, ...], attrs: dict[str, Any]) -> 'C':
        attrs = dict(attrs)
        orig_init = attrs.get("__init__")

        def __init__(self: _WorkflowMeta, *args: Any, **kwargs: Any) -> None:
            self.__fixp = _FixpointInstance(workflow_id=self.__fixp_meta.workflow.id)
            if orig_init:
                orig_init(self, *args, **kwargs)

        attrs["__init__"] = __init__
        attrs['__fixp_meta'] = fixp_meta
        attrs["__fixp"] = None

        return type.__new__(cls, name, bases, attrs)


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
    def inner(cls: Type[C]) -> Type[C]:
       attrs = dict(cls.__dict__)

       return cast(Type[C], _WorkflowMeta(_FixpointMeta(workflow_id=id), cls.__name__, cls.__bases__, attrs))

    return inner
