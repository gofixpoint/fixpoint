from typing import Any, Callable, Optional, ParamSpec, TypeVar, cast
from functools import wraps


class TaskFixp:
    id: str
    main: bool

    def __init__(self, id: str, main: bool = False):
        self.id = id
        self.main = main


Params = ParamSpec("Params")
Ret = TypeVar("Ret")


def task(
    id: str, *, main: bool = False
) -> Callable[[Callable[Params, Ret]], Callable[Params, Ret]]:
    def decorator(func: Callable[Params, Ret]) -> Callable[Params, Ret]:
        func.__fixp = TaskFixp(id, main)  # type: ignore[attr-defined]

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Ret:
            print("Before calling", func.__name__)
            result = func(*args, **kwargs)
            print("After calling", func.__name__)
            return result

        return cast(Callable[Params, Ret], wrapper)

    return decorator


def get_task_fixp(fn: Callable[..., Any]) -> Optional[TaskFixp]:
    return getattr(fn, "__fixp", None)
