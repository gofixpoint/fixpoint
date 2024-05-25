"""
TLRU Cache
"""

import time
from threading import RLock
from typing import Union, Any
from cachetools import TLRUCache as CachetoolsTLRUCache

from fixpoint.cache.protocol import SupportsTLRUCache, K_contra, V, SupportsTTLCacheItem


class TLRUCacheItem(SupportsTTLCacheItem):
    """
    TLRU Cache Item
    """

    def __init__(self, data: Any, ttl: float) -> None:
        self._data = data
        self._ttl = ttl

    def __repr__(self) -> str:
        return f"Item(data={self.data}, ttl={self.ttl})"

    @property
    def data(self) -> Any:
        return self._data

    @data.setter
    def data(self, value: V) -> None:
        self._data = value

    @property
    def ttl(self) -> float:
        return self._ttl

    @ttl.setter
    def ttl(self, value: float) -> None:
        self._ttl = value


class TLRUCache(SupportsTLRUCache[K_contra, V]):
    """
    TLRU Cache
    """

    def __init__(
        self,
        maxsize: int,
    ) -> None:

        def my_ttu(_key: K_contra, value: SupportsTTLCacheItem, now: float) -> float:
            # assume value.ttl contains the item's time-to-live in seconds
            return now + value.ttl

        self.cache = CachetoolsTLRUCache(
            maxsize=maxsize, ttu=my_ttu, timer=time.monotonic
        )

        self.lock = RLock()

    def get(self, key: K_contra) -> Union[Any, None]:
        with self.lock:
            item = self.cache.get(key)
            if item is not None:
                return item.data
            return None

    def set(self, key: K_contra, value: V, ttl: float) -> None:
        with self.lock:
            self.cache[key] = TLRUCacheItem(value, ttl)

    def delete(self, key: K_contra) -> None:
        with self.lock:
            del self.cache[key]

    def clear(self) -> None:
        with self.lock:
            self.cache.clear()

    @property
    def currentsize(self) -> int:
        """
        Get the current size of the cache
        """
        with self.lock:
            return int(self.cache.currsize)

    @property
    def maxsize(self) -> int:
        """
        Get the maxsize of the cache
        """
        with self.lock:
            return int(self.cache.maxsize)
