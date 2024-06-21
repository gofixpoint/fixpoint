import inspect
from typing import Any, Callable, ParamSpec, TypeVar

from .errors import DefinitionException


def validate_func_has_context_arg(func: Callable[..., Any]) -> None:
    sig = inspect.signature(func)
    if len(sig.parameters) < 1:
        raise DefinitionException(
            "Function must take at least one argument of type WorkflowContext"
        )
    first_param = [p for p in sig.parameters.values()][0]
    if first_param.name == "self":
        if len(sig.parameters) < 2:
            raise DefinitionException(
                "In class method: first non-self parameter must be of type WorkflowContext"
            )


Params = ParamSpec("Params")
Ret = TypeVar("Ret")
