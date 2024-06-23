"""Internal helpers for the structured workflow system"""

import inspect
from typing import Any, Callable, ParamSpec, TypeVar

from .errors import DefinitionException


def validate_func_has_context_arg(func: Callable[..., Any]) -> None:
    """Validate that a function has a WorkflowContext as its first argument

    If the function is a method, we expect the first argument to be "self" and
    the next argument to be a a WorkflowContext.
    """
    sig = inspect.signature(func)
    if len(sig.parameters) < 1:
        raise DefinitionException(
            "Function must take at least one argument of type WorkflowContext"
        )
    first_param = list(sig.parameters.values())[0]
    if first_param.name == "self":
        if len(sig.parameters) < 2:
            raise DefinitionException(
                "In class method: first non-self parameter must be of type WorkflowContext"
            )


Params = ParamSpec("Params")
Ret = TypeVar("Ret")
