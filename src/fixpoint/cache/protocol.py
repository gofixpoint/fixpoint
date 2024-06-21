"""Protocol definitions for various cache types"""

from typing import Any, Optional, Protocol, Type, TypeVar, Union

from pydantic import BaseModel

from fixpoint.completions import ChatCompletion
from ._shared import CreateChatCompletionRequest, BM


# Rename K to K_contra to indicate contravariance
K_contra = TypeVar("K_contra", contravariant=True)  # Key type
V = TypeVar("V")  # Value type


class SupportsCache(Protocol[K_contra, V]):
    """A basic cache protocol"""

    def get(self, key: K_contra) -> Union[V, None]:
        """Retrieve an item by key"""

    def set(self, key: K_contra, value: V) -> None:
        """Set an item by key"""

    def delete(self, key: K_contra) -> None:
        """Delete an item by key"""

    def clear(self) -> None:
        """Clear all items from the cache"""

    @property
    def maxsize(self) -> int:
        """Property to get the maxsize of the cache"""

    @property
    def currentsize(self) -> int:
        """Property to get the currentsize of the cache"""


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


class SupportCacheItem(Protocol[V_co]):
    """A basic cache item protocol"""

    @property
    def key(self) -> Any:
        """Property to get the key of the item"""

    @property
    def value(self) -> V_co:
        """Property to get the data of the item"""


__all__ = [
    "SupportsCache",
    "SupportsChatCompletionCache",
    "SupportCacheItem",
    "CreateChatCompletionRequest",
]
