"""A TLRU cache that stores items on disk"""

import tempfile
from typing import Optional, Union, Type, cast

import diskcache
from pydantic import BaseModel

from ..completions import ChatCompletion
from .protocol import (
    SupportsCache,
    K_contra,
    V,
    SupportsChatCompletionCache,
    CreateChatCompletionRequest,
)
from ._shared import logger, BM

# 50 MB
_DEFAULT_SIZE_LIMIT_BYTES = 50 * 1024 * 1024


class DiskTLRUCache(SupportsCache[K_contra, V]):
    """A TLRU cache that stores items on disk"""

    _ttl_s: float
    _cache: diskcache.Cache
    _size_limit_bytes: int

    def __init__(
        self,
        cache_dir: str,
        # TTL in seconds
        ttl_s: float,
        # 50 MB
        size_limit_bytes: int = _DEFAULT_SIZE_LIMIT_BYTES,
    ) -> None:
        self._cache = diskcache.Cache(directory=cache_dir, size_limit=size_limit_bytes)
        self._ttl_s = ttl_s
        self._size_limit_bytes = size_limit_bytes

    @classmethod
    def from_tmpdir(
        cls, ttl_s: float, size_limit_bytes: int = _DEFAULT_SIZE_LIMIT_BYTES
    ) -> "DiskTLRUCache[K_contra, V]":
        """Create a new cache from inside a temporary directory"""
        tmpdir = tempfile.mkdtemp()
        logger.debug("Created temporary directory for disk cache: %s", tmpdir)
        return cls(cache_dir=tmpdir, ttl_s=ttl_s, size_limit_bytes=size_limit_bytes)

    def get(self, key: K_contra) -> Union[V, None]:
        """Retrieve an item by key"""
        val = cast(Union[V, None], self._cache.get(key))
        if val is None:
            logger.debug("Cache miss for key: %s", key)
        else:
            logger.debug("Cache hit for key: %s", key)
        return val

    def set(self, key: K_contra, value: V) -> None:
        """Set an item by key"""
        logger.debug("Setting key: %s", key)
        self._cache.set(key, value, expire=self._ttl_s)

    def delete(self, key: K_contra) -> None:
        """Delete an item by key"""
        self._cache.delete(key)

    def clear(self) -> None:
        """Clear all items from the cache"""
        self._cache.clear()

    @property
    def maxsize(self) -> int:
        """Property to get the maxsize of the cache"""
        return self._size_limit_bytes

    @property
    def currentsize(self) -> int:
        """Property to get the currentsize of the cache"""
        return cast(int, self._cache.volume())


# Pydantic models do not pickle well, so make a class that serializes and
# deserializes the ChatCompletion
class ChatCompletionDiskTLRUCache(
    DiskTLRUCache[CreateChatCompletionRequest[BaseModel], ChatCompletion[BaseModel]],
    SupportsChatCompletionCache,
):
    """A TLRU cache that stores chat completions on disk"""

    @classmethod
    def from_tmpdir(
        cls, ttl_s: float, size_limit_bytes: int = _DEFAULT_SIZE_LIMIT_BYTES
    ) -> "ChatCompletionDiskTLRUCache":
        """Create a new cache from inside a temporary directory"""
        tmpdir = tempfile.mkdtemp()
        logger.debug("Created temporary directory for disk cache: %s", tmpdir)
        return cls(cache_dir=tmpdir, ttl_s=ttl_s, size_limit_bytes=size_limit_bytes)

    def set(
        self, key: CreateChatCompletionRequest[BM], value: ChatCompletion[BM]
    ) -> None:
        """Set an item by key"""
        logger.debug("Setting key: %s", key)
        value_str = value.serialize_json()
        self._cache.set(key, value_str, expire=self._ttl_s)

    def get(
        self,
        key: CreateChatCompletionRequest[BM],
        response_model: Optional[Type[BM]] = None,
    ) -> Union[ChatCompletion[BM], None]:
        """Retrieve an item by key"""
        val_str = self._cache.get(key)
        if val_str is None:
            logger.debug("Cache miss for key: %s", key)
            return None

        logger.debug("Cache hit for key: %s", key)
        val = ChatCompletion[BM].deserialize_json(
            val_str, response_model=response_model
        )
        return val
