import inspect
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

from ._workflow import workflow_entrypoint, get_workflow_definition_meta_fixp
from ._task import task_entrypoint, get_task_definition_meta_fixp
from ._helpers import Params, Ret
from ._helpers import DefinitionException


def entrypoint() -> Callable[[Callable[Params, Ret]], Callable[Params, Ret]]:
    def decorator(func: Callable[Params, Ret]) -> Callable[Params, Ret]:
        import ipdb; ipdb.set_trace()

        if not inspect.ismethod(func):
            raise DefinitionException(f"Entrypoint {func} is not a method")

        func.__self__
        fixp = getattr()

    return decorator
