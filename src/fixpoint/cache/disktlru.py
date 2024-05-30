"""A TLRU cache that stores items on disk"""

import tempfile
from typing import Union, cast

import diskcache

from .protocol import SupportsCache, K_contra, V
from ._shared import hash_key, logger

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
        hashed = hash_key(key)
        val = cast(Union[V, None], self._cache.get(hashed))
        if val is None:
            logger.debug("Cache miss for key: %d", hashed)
        else:
            logger.debug("Cache hit for key: %d", hashed)
        return val

    def set(self, key: K_contra, value: V) -> None:
        """Set an item by key"""
        hashed = hash_key(key)
        logger.debug("Setting key: %d", hashed)
        self._cache.set(hashed, value, expire=self._ttl_s)

    def delete(self, key: K_contra) -> None:
        """Delete an item by key"""
        self._cache.delete(hash_key(key))

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
