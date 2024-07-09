"""Internal shared code for the "agents" module."""

__all__ = [
    "request_cached_completion",
    "arequest_cached_completion",
    "CacheMode",
    "random_agent_id",
]


import asyncio
from typing import Callable, Coroutine, Literal, Never, Optional, TypeVar

from pydantic import BaseModel

from fixpoint._utils.ids import make_resource_uuid
from fixpoint.cache import SupportsChatCompletionCache, CreateChatCompletionRequest
from ..completions import ChatCompletion


# Types of cache modes:
#
# - skip_lookup: Don't look up keys in the cache, but write results to the
#   cache.
# - skip_all: Don't look up the cache, and don't store the result.
# - normal: Look up the cache, and store the result if it's not in the cache.
CacheMode = Literal["skip_lookup", "skip_all", "normal"]


T = TypeVar("T", bound=BaseModel)


def request_cached_completion(
    cache: Optional[SupportsChatCompletionCache],
    req: CreateChatCompletionRequest[T],
    completion_fn: Callable[[], ChatCompletion[T]],
    cache_mode: Optional[CacheMode],
) -> ChatCompletion[T]:
    """Request a completion and optionally lookup/store it in the cache.

    completion_fn should be a function that takes no arguments and returns a
    ChatCompletion. In practice, you want to create a function that wraps the
    real chat completion request function, and that function takes all its
    needed arguments.
    """
    if cache is None:
        return completion_fn()

    cmpl = None
    if cache_mode not in ("skip_lookup", "skip_all"):
        cmpl = cache.get(req, response_model=req["response_model"])
    if cmpl is None:
        cmpl = completion_fn()
        if cache_mode != "skip_all":
            cache.set(req, cmpl)

    return cmpl


async def arequest_cached_completion(
    cache: Optional[SupportsChatCompletionCache],
    req: CreateChatCompletionRequest[T],
    completion_fn: Callable[[], Coroutine[Never, Never, ChatCompletion[T]]],
    cache_mode: Optional[CacheMode],
) -> ChatCompletion[T]:
    """Request an completion and optionally lookup/store it in the cache.

    completion_fn should be an async function that takes no arguments and
    returns a ChatCompletion. In practice, you want to create a function that
    wraps the real chat completion request function, and that function takes all
    its needed arguments.
    """
    if cache is None:
        async with asyncio.TaskGroup() as tg:
            cmpl_task = tg.create_task(completion_fn())
        return cmpl_task.result()

    cmpl = None
    if cache_mode not in ("skip_lookup", "skip_all"):
        cmpl = cache.get(req, response_model=req["response_model"])
    if cmpl is None:
        async with asyncio.TaskGroup() as tg:
            cmpl_task = tg.create_task(completion_fn())
        cmpl = cmpl_task.result()
        if cache_mode != "skip_all":
            cache.set(req, cmpl)

    return cmpl


def random_agent_id() -> str:
    """Generate a random agent ID if not explicitly given"""
    return make_resource_uuid("agent")
