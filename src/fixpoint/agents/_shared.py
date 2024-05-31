"""Internal shared code for the "agents" module."""

from typing import Callable, List, Optional, Literal, Type, TypeVar, cast

from pydantic import BaseModel

from ..cache import SupportsChatCompletionCache
from ..completions import ChatCompletionMessageParam, ChatCompletion


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
    messages: List[ChatCompletionMessageParam],
    completion_fn: Callable[[], ChatCompletion[T]],
    cache_mode: Optional[CacheMode],
    response_model: Optional[Type[T]],
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
        cmpl = cache.get(messages, response_model=response_model)
    if cmpl is None:
        cmpl = completion_fn()
        if cache_mode != "skip_all":
            # cast the type to resolve this error:
            #
            #     Argument 2 to "set" of "SupportsCache" has incompatible type
            #     "ChatCompletion[T]"; expected "ChatCompletion[BaseModel]"
            cache.set(messages, cast(ChatCompletion[BaseModel], cmpl))

    return cmpl
