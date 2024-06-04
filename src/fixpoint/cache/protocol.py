"""Protocol definitions for various cache types"""

from typing import List, Optional, Protocol, TypeVar, Union, Any, Type

from pydantic import BaseModel

from fixpoint.completions.chat_completion import ChatCompletion
from fixpoint.completions.chat_completion import ChatCompletionMessageParam


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


T = TypeVar("T", bound=BaseModel)


# Pydantic models do not pickle well, so make a class that serializes and
# deserializes the ChatCompletion. To do deserialization, we need to know the
# BaseModel class to use.
class SupportsChatCompletionCache(
    SupportsCache[List[ChatCompletionMessageParam], ChatCompletion[BaseModel]], Protocol
):
    """A cache protocol for chat completions"""

    def get(
        self,
        key: List[ChatCompletionMessageParam],
        response_model: Optional[Type[T]] = None,
    ) -> Union[ChatCompletion[T], None]:
        """Retrieve an item by key, optionally populating the structured output field"""


V_co = TypeVar("V_co", covariant=True)


class SupportCacheItem(Protocol[V_co]):
    """A basic cache item protocol"""

    @property
    def key(self) -> Any:
        """Property to get the key of the item"""

    @property
    def value(self) -> V_co:
        """Property to get the data of the item"""


class SupportsTTLCacheItem(SupportCacheItem[V_co], Protocol):
    """Protocol for a Time-Limited LRU cache item"""

    @property
    def ttl(self) -> float:
        """Property to get the TTL of the item"""

    @property
    def expires_at(self) -> float:
        """Property to get the expiration time of the item"""
