"""
TLRU Cache for chat completions
"""

import time
from dataclasses import dataclass
from threading import RLock
from typing import Any, Generic, Union, Optional, Type, cast
from cachetools import TLRUCache as CachetoolsTLRUCache

from pydantic import BaseModel

from ..completions.chat_completion import ChatCompletion
from .protocol import (
    SupportsChatCompletionCache,
    CreateChatCompletionRequest,
)
from .._storage.protocol import SupportsStorage, SupportsSerialization
from ._shared import (
    BM,
    serialize_chat_completion_request,
    deserialize_chat_completion_request,
)


class ChatCompletionTLRUCacheItem(
    SupportsSerialization["ChatCompletionTLRUCacheItem[BM]"], Generic[BM]
):
    """
    TLRU Cache Item
    """

    _key: CreateChatCompletionRequest[BM]
    _value: ChatCompletion[BM]
    _ttl: float
    _expires_at: float

    def __init__(
        self,
        key: CreateChatCompletionRequest[BM],
        value: ChatCompletion[BM],
        ttl: float,
        expires_at: Union[float, None] = None,
    ) -> None:
        self._key = key
        self._value = value
        self._ttl = ttl
        self._expires_at = (
            expires_at if expires_at is not None else self._calc_expires_at()
        )

    def __repr__(self) -> str:
        return (
            f"Item(key={self.key}, value={self.value}, "
            f"ttl={self.ttl}, expires_at={self._expires_at})"
        )

    def _calc_expires_at(self) -> float:
        return time.monotonic() + self._ttl

    @property
    def key(self) -> CreateChatCompletionRequest[BM]:
        """Get the key"""
        return self._key

    @key.setter
    def key(self, key: CreateChatCompletionRequest[BM]) -> None:
        """Set the key"""
        self._key = key

    @property
    def value(self) -> ChatCompletion[BM]:
        """Get the value"""
        return self._value

    @value.setter
    def value(self, value: ChatCompletion[BM]) -> None:
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
            "key": serialize_chat_completion_request(self._key),
            "value": self._value.serialize_json(),
            "ttl": self._ttl,
            "expires_at": self._expires_at,
        }

    @classmethod
    def deserialize(
        cls, data: dict[str, Any], response_model: Optional[Type[BM]] = None
    ) -> "ChatCompletionTLRUCacheItem[BM]":
        """Deserialize a dictionary into a TLRUCacheItem"""
        key: CreateChatCompletionRequest[BM] = deserialize_chat_completion_request(
            data.pop("key"),
            response_model=response_model,
        )
        value: ChatCompletion[BM] = ChatCompletion.deserialize_json(
            data.pop("value"), response_model
        )
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


class ChatCompletionTLRUCache(SupportsChatCompletionCache):
    """A TLRU cache for LLM inference requests"""

    _ttl_s: float

    cache: CachetoolsTLRUCache[str, ChatCompletionTLRUCacheItem[BaseModel]]
    _storage: Optional[SupportsStorage[ChatCompletionTLRUCacheItem[BaseModel]]]
    _storage_options: Optional[StorageOptions]

    def __init__(
        self,
        maxsize: int,
        ttl_s: float,
        storage: Optional[
            SupportsStorage[ChatCompletionTLRUCacheItem[BaseModel]]
        ] = None,
        storage_options: Optional[StorageOptions] = None,
    ) -> None:
        """
        max_size: the max number of items to keep in the cache
        ttl_s: the time-to-live in seconds per item
        serialize_key_fn: a function that converts the key to a string for serialization
        deserialize_key_fn: a function that converts a string to the key for deserialization
        serialize_value_fn: a function that converts the value to a string for serialization
        deserialize_value_fn: a function that converts a string to the value for deserialization
        storage: an optional storage to persist the cache to
        storage_options: if storage is specified, this lets you configure it
        """

        def my_ttu(
            _key: str, value: ChatCompletionTLRUCacheItem[BaseModel], now: float
        ) -> float:
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
                # TODO(dbmikus) this does not load in the structured output
                _key: str = serialize_chat_completion_request(cache_item.key)
                self.cache[_key] = cache_item

            # Remove expired items from the storage
            expired_items = [
                item for item in deserialized_results if item.expires_at < current_time
            ]
            for cache_item in expired_items:
                _key = serialize_chat_completion_request(cache_item.key)
                self._storage.delete(_key)

    def get(
        self,
        key: CreateChatCompletionRequest[BM],
        response_model: Optional[Type[BM]] = None,
    ) -> Union[ChatCompletion[BM], None]:
        with self.lock:
            # Pre-emptively expire any expired items
            self.cache.expire()
            _key = serialize_chat_completion_request(key)
            item = self.cache.get(_key)
            if item is not None:
                if response_model is None:
                    if item.value.fixp.structured_output is not None:
                        raise ValueError(
                            "the completion's structured output should be None"
                        )
                    return cast(ChatCompletion[BM], item.value)
                elif not isinstance(item.value.fixp.structured_output, response_model):
                    raise ValueError(
                        f"Item's structured_output should be of type: {response_model}"
                    )
                return cast(ChatCompletion[BM], item.value)
            return None

    def set(
        self, key: CreateChatCompletionRequest[BM], value: ChatCompletion[BM]
    ) -> None:
        with self.lock:
            cache_item = ChatCompletionTLRUCacheItem(
                key,
                value,
                self._ttl_s,
            )
            self.cache[serialize_chat_completion_request(key)] = cast(
                ChatCompletionTLRUCacheItem[BaseModel], cache_item
            )
            if self._supports_persist_to_storage() and self._storage is not None:
                self._storage.insert(
                    cast(ChatCompletionTLRUCacheItem[BaseModel], cache_item)
                )

    def delete(self, key: CreateChatCompletionRequest[BM]) -> None:
        with self.lock:
            _key = serialize_chat_completion_request(key)
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
