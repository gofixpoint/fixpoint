from functools import wraps
import inspect
from typing import Any, Callable, Dict, List, Optional, cast

from fixpoint_extras.workflows.imperative import WorkflowContext
from .errors import DefinitionException
from ._helpers import validate_func_has_context_arg, Params, Ret


class StepFixp:
    id: str

    def __init__(self, id: str):
        self.id = id


def step(
    id: str,
) -> Callable[[Callable[Params, Ret]], Callable[Params, Ret]]:
    def decorator(func: Callable[Params, Ret]) -> Callable[Params, Ret]:
        func.__fixp = StepFixp(id)  # type: ignore[attr-defined]

        validate_func_has_context_arg(func)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Ret:
            print("Before calling", func.__name__)
            result = func(*args, **kwargs)
            print("After calling", func.__name__)
            return result

        return cast(Callable[Params, Ret], wrapper)

    return decorator


def get_step_fixp(fn: Callable[..., Any]) -> Optional[StepFixp]:
    if not callable(fn):
        return None
    attr = getattr(fn, "__fixp", None)
    if isinstance(attr, StepFixp):
        return attr
    return None


def call_step(
    ctx: WorkflowContext,
    fn: Callable[Params, Ret],
    args: Optional[List[Any]] = None,
    kwargs: Optional[Dict[str, Any]] = None,
) -> Ret:
    args = args or []
    kwargs = kwargs or {}

    step_fixp = get_step_fixp(fn)
    if not step_fixp:
        raise DefinitionException(f"Step {fn.__name__} is not a valid step definition")

    ret = fn(ctx, *args, **kwargs)  # type: ignore[arg-type]
    return ret
