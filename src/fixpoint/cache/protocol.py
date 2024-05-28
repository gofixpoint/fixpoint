"""Protocol definitions for various cache types"""

from typing import Protocol, TypeVar, Union, Any

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


class SupportCacheItem(Protocol):
    """A basic cache item protocol"""

    @property
    def data(self) -> Any:
        """Property to get the data of the item"""


class SupportsTTLCacheItem(SupportCacheItem, Protocol):
    """Protocol for a Time-Limited LRU cache item"""

    @property
    def ttl(self) -> float:
        """Property to get the TTL of the item"""
