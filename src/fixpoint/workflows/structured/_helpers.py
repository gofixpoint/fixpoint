"""Internal helpers for the structured workflow system"""

import asyncio
from functools import wraps
import inspect
from typing import Any, Awaitable, Callable, Coroutine, ParamSpec, Tuple, TypeVar, cast

from ._context import WorkflowContext
from .errors import CallException, DefinitionException, InternalException
from ._callcache import CallCacheKind, CacheResult, serialize_args


Params = ParamSpec("Params")
Ret = TypeVar("Ret")
Ret_co = TypeVar("Ret_co", covariant=True)
AwaitableRet = TypeVar("AwaitableRet", bound=Awaitable[Any])
AsyncFunc = Callable[Params, Coroutine[Any, Any, Ret]]


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


def decorate_with_cache(
    kind: CallCacheKind, kind_id: str
) -> Callable[[AsyncFunc[Params, Ret]], AsyncFunc[Params, Ret]]:
    """Decorate a task or a step for call durability.

    Decorate a step or a task for call durability, so that we store the results
    of calling a task or a step. If the workflow fails and we recall the task or
    step, we can check if we already computed its results.
    """

    def decorator(func: AsyncFunc[Params, Ret]) -> AsyncFunc[Params, Ret]:
        validate_func_has_context_arg(func)

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Ret:
            ctx, ctx_pos = _pull_ctx_arg(*args)
            wrun_id = ctx.workflow_run.id
            if kind == CallCacheKind.TASK:
                callcache = ctx.run_config.call_cache.tasks
            elif kind == CallCacheKind.STEP:
                callcache = ctx.run_config.call_cache.steps
            else:
                raise InternalException(f"Unknown call cache kind: {kind}")

            remaining_args = args[ctx_pos + 1 :]
            serialized = serialize_args(*remaining_args, **kwargs)
            cache_check: CacheResult[Ret] = callcache.check_cache(
                run_id=wrun_id, kind_id=kind_id, serialized_args=serialized
            )
            # TODO(dbmikus) push a WorkflowContext task/step transition onto our call stack
            match cache_check:
                case CacheResult(found=True, result=cache_res):
                    # we can cast this, because while `cache_res` is of type
                    # Optional[Ret], if `found is True`, then `cache_res` is
                    # actually of type `Ret`.
                    #
                    # We can't just do an `is None` check, because technically
                    # the result could be of type `None`.
                    return cast(Ret, cache_res)

            async with asyncio.TaskGroup() as tg:
                res_task = tg.create_task(func(*args, **kwargs))
            res = res_task.result()
            callcache.store_result(
                run_id=wrun_id, kind_id=kind_id, serialized_args=serialized, res=res
            )
            return res

        return wrapper

    return decorator


def _pull_ctx_arg(*args: Any) -> Tuple[WorkflowContext, int]:
    """Return the WorkflowContext from function params, along with its position.

    Return the WorkflowContext argument and its position in the args, which will
    either be 0 or 1. If the function is a method, we can skip the first
    argument because it will be `self`.

    Raises a CallException if the WorkflowContext is not found.
    """
    if len(args) == 0:
        raise _new_workflow_context_expected_exc()
    if isinstance(args[0], WorkflowContext):
        return args[0], 0
    if len(args) <= 1:
        raise _new_workflow_context_expected_exc()
    if isinstance(args[1], WorkflowContext):
        return args[1], 1
    raise _new_workflow_context_expected_exc()


def _new_workflow_context_expected_exc() -> CallException:
    return CallException("Expected WorkflowContext as first argument")
