"""
TLRU Cache
"""

import time
from threading import RLock
from typing import Any, Callable, List, Union, Optional, Type, TypeVar, cast
from cachetools import TLRUCache as CachetoolsTLRUCache

from pydantic import BaseModel

from ..completions.chat_completion import ChatCompletion, ChatCompletionMessageParam
from .protocol import (
    SupportsCache,
    K_contra,
    V,
    SupportsTTLCacheItem,
    SupportsChatCompletionCache,
)


class TLRUCacheItem(SupportsTTLCacheItem[V]):
    """
    TLRU Cache Item
    """

    _key: Any
    _value: V
    _ttl: float
    _created_at: float
    _serialize_fn: Callable[[Any], str]

    def __init__(
        self, key: Any, value: V, ttl: float, _serialize_fn: Callable[[Any], str]
    ) -> None:
        self._key = key
        self._value = value
        self._ttl = ttl
        self._created_at = time.monotonic()
        self._serialize_fn = _serialize_fn

    def __repr__(self) -> str:
        return (
            f"Item(key={self.key}, value={self.value}, "
            f"ttl={self.ttl}, created_at={self._created_at})"
        )

    @property
    def key(self) -> Any:
        return self._key

    @key.setter
    def key(self, value: K_contra) -> None:
        self._key = value

    @property
    def value(self) -> V:
        return self._value

    @value.setter
    def value(self, value: V) -> None:
        self._value = value

    @property
    def ttl(self) -> float:
        return self._ttl

    @ttl.setter
    def ttl(self, value: float) -> None:
        self._ttl = value

    @property
    def created_at(self) -> float:
        """Property to get the creation time of the item"""
        return self._created_at

    def to_dict(self) -> dict[str, Any]:
        """Convert the item to a dictionary"""
        return {
            "key": self._key,
            "value": self._serialize_fn(self._value),
            "ttl": self._ttl,
            "created_at": self._created_at,
        }


class TLRUCache(SupportsCache[K_contra, V]):
    """
    TLRU Cache
    """

    _ttl: float
    _serialize_key_fn: Callable[[K_contra], str]
    cache: CachetoolsTLRUCache[str, TLRUCacheItem[V]]

    def __init__(
        self, maxsize: int, ttl: float, serialize_key_fn: Callable[[K_contra], str]
    ) -> None:

        def my_ttu(_key: str, value: SupportsTTLCacheItem[V], now: float) -> float:
            # assume value.ttl contains the item's time-to-live in seconds
            return now + value.ttl

        self.cache = CachetoolsTLRUCache(
            maxsize=maxsize, ttu=my_ttu, timer=time.monotonic
        )

        self.lock = RLock()
        self._ttl = ttl
        self._serialize_key_fn = serialize_key_fn

    def _serialize_key(self, key: K_contra) -> str:
        return self._serialize_key_fn(key)

    def get(self, key: K_contra) -> Union[Any, None]:
        with self.lock:
            # Pre-emptively expire any expired items
            self.cache.expire()
            _key_hash = self._serialize_key(key)
            item = self.cache.get(_key_hash)
            if item is not None:
                return item.value
            return None

    def set(self, key: K_contra, value: V) -> None:
        with self.lock:
            _key_hash = self._serialize_key(key)
            self.cache[_key_hash] = TLRUCacheItem(
                key, value, self._ttl, self._serialize_key
            )

    def delete(self, key: K_contra) -> None:
        with self.lock:
            _key_hash = self._serialize_key(key)
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


T = TypeVar("T", bound=BaseModel)


class ChatCompletionTLRUCache(
    TLRUCache[List[ChatCompletionMessageParam], ChatCompletion[BaseModel]],
    SupportsChatCompletionCache,
):
    """A TLRU cache for LLM inference requests"""

    def get(
        self,
        key: List[ChatCompletionMessageParam],
        # pylint: disable=unused-argument
        response_model: Optional[Type[T]] = None,
    ) -> Union[ChatCompletion[T], None]:
        # this cache doesn't need to serialize/deserialize anything because
        # we're in the Python memory. So we can ignore the structured_data_cls
        return cast(ChatCompletion[T], super().get(key))
