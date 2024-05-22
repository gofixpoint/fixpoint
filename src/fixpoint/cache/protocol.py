"""Protocol definitions for various cache types"""

from typing import Protocol, TypeVar

# Rename K to K_contra to indicate contravariance
K_contra = TypeVar("K_contra", contravariant=True)  # Key type
V = TypeVar("V")  # Value type


class Cache(Protocol[K_contra, V]):
    """A basic cache protocol"""

    def get(self, key: K_contra) -> V:
        """Retrieve an item by key"""

    def set(self, key: K_contra, value: V) -> None:
        """Set an item by key"""

    def delete(self, key: K_contra) -> None:
        """Delete an item by key"""

    def clear(self) -> None:
        """Clear all items from the cache"""


class LRUCache(Cache[K_contra, V], Protocol[K_contra, V]):
    """Protocol for an LRU cache"""

    def get(self, key: K_contra) -> V:
        """Retrieve an item by key, updating LRU order"""

    def set(self, key: K_contra, value: V) -> None:
        """Set an item by key, possibly evicting the least recently used item"""

    def delete(self, key: K_contra) -> None:
        """Delete an item by key"""

    def clear(self) -> None:
        """Clear all items from the cache"""


class TLRUCache(Protocol[K_contra, V]):
    """Protocol for a Time-Limited LRU cache"""

    def get(self, key: K_contra) -> V:
        """Retrieve an item by key if it has not expired, updating LRU order"""

    def set(self, key: K_contra, value: V, ttl: int) -> None:
        """Set an item by key with a time-to-live (TTL)"""

    def delete(self, key: K_contra) -> None:
        """Delete an item by key"""

    def clear(self) -> None:
        """Clear all items from the cache"""
