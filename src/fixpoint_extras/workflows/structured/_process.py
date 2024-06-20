from typing import Any, Awaitable, Callable, Dict, List, Optional, Type, TypeVar

from ._helpers import Params, Ret
from ._task import get_task_entrypoint_fixp_from_fn
from ._step import get_step_fixp


C = TypeVar("C")

async def call_step(
    fn: Callable[Params, Ret],
    args: Optional[List[Any]] = None,
    kwargs: Optional[Dict[str, Any]] = None,
) -> Ret:
    args = args or []
    kwargs = kwargs or {}

    task_fixp = get_task_entrypoint_fixp_from_fn()

    return fn(*args, **kwargs)
