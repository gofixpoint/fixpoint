"""Protocol definitions for various cache types"""

from typing import Optional, Protocol, Type, TypeVar, Union

from pydantic import BaseModel

from fixpoint.completions import ChatCompletion
from ._shared import CreateChatCompletionRequest, BM
from ._genericcache.protocol import SupportsCache


# Pydantic models do not pickle well, so make a class that serializes and
# deserializes the ChatCompletion. To do deserialization, we need to know the
# BaseModel class to use.
class SupportsChatCompletionCache(
    SupportsCache[CreateChatCompletionRequest[BaseModel], ChatCompletion[BaseModel]],
    Protocol,
):
    """A cache protocol for chat completions"""

    def get(
        self,
        key: CreateChatCompletionRequest[BM],
        response_model: Optional[Type[BM]] = None,
    ) -> Union[ChatCompletion[BM], None]:
        """Retrieve an item by key, optionally populating the structured output field"""

    def set(
        self, key: CreateChatCompletionRequest[BM], value: ChatCompletion[BM]
    ) -> None:
        """Set an item by key"""


V_co = TypeVar("V_co", covariant=True)


__all__ = [
    "SupportsCache",
    "SupportsChatCompletionCache",
    "CreateChatCompletionRequest",
]
