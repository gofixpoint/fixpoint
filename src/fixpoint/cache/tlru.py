"""
TLRU Cache
"""

import time
from threading import RLock
from typing import Union, Any
from cachetools import TLRUCache as CachetoolsTLRUCache

from .protocol import SupportsCache, K_contra, V, SupportsTTLCacheItem
from ._shared import hash_key


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


class TLRUCache(SupportsCache[K_contra, V]):
    """
    TLRU Cache
    """

    def __init__(
        self,
        maxsize: int,
        ttl: float,
    ) -> None:

        def my_ttu(_key: int, value: SupportsTTLCacheItem, now: float) -> float:
            # assume value.ttl contains the item's time-to-live in seconds
            return now + value.ttl

        self.cache = CachetoolsTLRUCache(
            maxsize=maxsize, ttu=my_ttu, timer=time.monotonic
        )

        self.lock = RLock()
        self._ttl = ttl

    def _hash_key(self, key: K_contra) -> int:
        return hash_key(key)

    def get(self, key: K_contra) -> Union[Any, None]:
        with self.lock:
            # Pre-emptively expire any expired items
            self.cache.expire()
            _key_hash = self._hash_key(key)
            item = self.cache.get(_key_hash)
            if item is not None:
                return item.data
            return None

    def set(self, key: K_contra, value: V) -> None:
        with self.lock:
            _key_hash = self._hash_key(key)
            self.cache[_key_hash] = TLRUCacheItem(value, self._ttl)

    def delete(self, key: K_contra) -> None:
        with self.lock:
            _key_hash = self._hash_key(key)
            del self.cache[_key_hash]

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
