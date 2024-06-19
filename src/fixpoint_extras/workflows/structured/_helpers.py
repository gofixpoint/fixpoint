import inspect
from typing import Any, Callable

from .errors import DefinitionError

def validate_func_has_context_arg(func: Callable[..., Any]):
    sig = inspect.signature(func)
    if len(sig.parameters) < 1:
        raise DefinitionError("Task must take at least one argument of type WorkflowContext")
    first_param = [p for p in sig.parameters.values()][0]
    if first_param.name == 'self':
        if len(sig.parameters) < 2:
            raise DefinitionError("In class method: first non-self parameter must be of type WorkflowContext")
