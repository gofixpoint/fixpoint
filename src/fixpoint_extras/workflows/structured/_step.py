from functools import wraps
import inspect
from typing import Any, Callable, Optional, ParamSpec, TypeVar, cast

from ._helpers import validate_func_has_context_arg


class StepFixp:
    id: str
    main: bool

    def __init__(self, id: str, main: bool = False):
        self.id = id
        self.main = main


Params = ParamSpec("Params")
Ret = TypeVar("Ret")


def step(
    id: str, *, main: bool = False
) -> Callable[[Callable[Params, Ret]], Callable[Params, Ret]]:
    def decorator(func: Callable[Params, Ret]) -> Callable[Params, Ret]:
        func.__fixp = StepFixp(id, main)  # type: ignore[attr-defined]

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
    attr = getattr(fn, "__fixp", None)
    if isinstance(attr, StepFixp):
        return attr
    return None
