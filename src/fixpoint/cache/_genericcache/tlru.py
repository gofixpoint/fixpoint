"""
TLRU Cache
"""

import time
import json
from dataclasses import dataclass
from threading import RLock
from typing import Any, Callable, Generic, Union, Optional
from cachetools import TLRUCache as CachetoolsTLRUCache

from fixpoint._storage.protocol import SupportsStorage, SupportsSerialization
from .protocol import (
    SupportsCache,
    K_contra,
    V,
)


class TLRUCacheItem(SupportsSerialization["TLRUCacheItem[V]"], Generic[V]):
    """
    TLRU Cache Item
    """

    _key: Any
    _value: V
    _ttl: float
    _expires_at: float
    _serialize_fn: Callable[[Any], str] = (
        json.dumps
    )  # Default serialization function at class level
    _deserialize_fn: Callable[[str], Any] = (
        json.loads
    )  # Default deserialization function at class level

    def __init__(
        self,
        key: Any,
        value: V,
        ttl: float,
        serialize_fn: Callable[[Any], str] = json.dumps,
        deserialize_fn: Callable[[str], Any] = json.loads,
        expires_at: Union[float, None] = None,
    ) -> None:
        self._key = key
        self._value = value
        self._ttl = ttl
        self._expires_at = (
            expires_at if expires_at is not None else self._calc_expires_at()
        )
        self._serialize_fn = serialize_fn
        self._deserialize_fn = deserialize_fn

    def __repr__(self) -> str:
        return (
            f"Item(key={self.key}, value={self.value}, "
            f"ttl={self.ttl}, expires_at={self._expires_at})"
        )

    def _calc_expires_at(self) -> float:
        return time.monotonic() + self._ttl

    @property
    def key(self) -> Any:
        """Get the key"""
        return self._key

    @key.setter
    def key(self, key: K_contra) -> None:
        """Set the key"""
        self._key = key

    @property
    def value(self) -> V:
        """Get the value"""
        return self._value

    @value.setter
    def value(self, value: V) -> None:
        """Set the value"""
        self._value = value

    @property
    def ttl(self) -> float:
        """Get the ttl"""
        return self._ttl

    @ttl.setter
    def ttl(self, ttl: float) -> None:
        """Set the ttl"""
        self._ttl = ttl

    @property
    def expires_at(self) -> float:
        """Property to get the creation time of the item"""
        return self._expires_at

    @expires_at.setter
    def expires_at(self, expires_at: float) -> None:
        self._expires_at = expires_at

    def serialize(self) -> dict[str, Any]:
        """Convert the item to a dictionary"""
        return {
            "key": self._serialize_fn(self._key),
            "value": self._serialize_fn(self._value),
            "ttl": self._ttl,
            "expires_at": self._expires_at,
        }

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> "TLRUCacheItem[V]":
        """Deserialize a dictionary into a TLRUCacheItem"""
        key = cls._deserialize_fn(data.pop("key"))
        value = cls._deserialize_fn(data.pop("value"))
        expires_at = data.pop("expires_at")
        return cls(**data, key=key, value=value, expires_at=expires_at)


@dataclass
class StorageOptions:
    """
    Storage Options
    """

    init_from_storage: bool
    persist_to_storage: bool

    def __init__(
        self,
        init_from_storage: bool = True,
        persist_to_storage: bool = True,
    ) -> None:
        self.init_from_storage = init_from_storage
        self.persist_to_storage = persist_to_storage


class TLRUCache(SupportsCache[K_contra, V]):
    """
    TLRU Cache
    """

    _ttl_s: float
    _serialize_key_fn: Callable[[K_contra], str]
    cache: CachetoolsTLRUCache[str, TLRUCacheItem[V]]
    _storage: Optional[SupportsStorage[TLRUCacheItem[V]]]
    _storage_options: Optional[StorageOptions]

    def __init__(
        self,
        maxsize: int,
        ttl_s: float,
        serialize_key_fn: Callable[[K_contra], str],
        storage: Optional[SupportsStorage[TLRUCacheItem[V]]] = None,
        storage_options: Optional[StorageOptions] = None,
    ) -> None:
        """
        max_size: the max number of items to keep in the cache
        ttl_s: the time-to-live in seconds per item
        serialize_key_fn: a function that converts a key to a string for serialization
        storage: an optional storage to persist the cache to
        storage_options: if storage is specified, this lets you configure it
        """

        def my_ttu(_key: str, value: TLRUCacheItem[V], now: float) -> float:
            # assume value.ttl contains the item's time-to-live in seconds
            return now + value.ttl

        self.cache = CachetoolsTLRUCache(
            maxsize=maxsize, ttu=my_ttu, timer=time.monotonic
        )
        self._storage = storage
        if self._storage is not None:
            self._storage_options = (
                StorageOptions(
                    init_from_storage=True,
                    persist_to_storage=True,
                )
                if storage_options is None
                else storage_options
            )
        else:
            self._storage_options = None

        self.lock = RLock()
        self._ttl_s = ttl_s
        self._serialize_key_fn = serialize_key_fn

        if self._supports_init_from_storage():
            self._init_from_storage()

    def _supports_init_from_storage(self) -> bool:
        return (
            self._storage is not None
            and self._storage_options is not None
            and self._storage_options.init_from_storage
        )

    def _supports_persist_to_storage(self) -> bool:
        return (
            self._storage is not None
            and self._storage_options is not None
            and self._storage_options.init_from_storage
        )

    def _init_from_storage(self) -> None:
        """Initialize the cache from the storage"""
        if self._storage is not None:
            # Not an ideal solution, because requires client-side expiration
            deserialized_results = self._storage.fetch_latest(n=self.maxsize)
            current_time = time.monotonic()

            # Add non-expired-items to the cache
            non_expired_items = [
                item for item in deserialized_results if item.expires_at >= current_time
            ]
            for cache_item in non_expired_items:
                _key = self._serialize_key(cache_item.key)
                self.cache[_key] = cache_item

            # Remove expired items from the storage
            expired_items = [
                item for item in deserialized_results if item.expires_at < current_time
            ]
            for cache_item in expired_items:
                _key = self._serialize_key(cache_item.key)
                self._storage.delete(_key)

    def _serialize_key(self, key: K_contra) -> str:
        return self._serialize_key_fn(key)

    def get(self, key: K_contra) -> Union[Any, None]:
        with self.lock:
            # Pre-emptively expire any expired items
            self.cache.expire()
            _key = self._serialize_key(key)
            item = self.cache.get(_key)
            if item is not None:
                return item.value
            return None

    def set(self, key: K_contra, value: V) -> None:
        with self.lock:
            _key = self._serialize_key(key)
            cache_item = TLRUCacheItem(key, value, self._ttl_s)
            self.cache[_key] = cache_item
            if self._supports_persist_to_storage() and self._storage is not None:
                self._storage.insert(cache_item)

    def delete(self, key: K_contra) -> None:
        with self.lock:
            _key = self._serialize_key(key)
            del self.cache[_key]
            if self._supports_persist_to_storage() and self._storage is not None:
                self._storage.delete(_key)

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
