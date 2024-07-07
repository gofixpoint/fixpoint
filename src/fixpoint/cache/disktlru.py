"""A TLRU cache that stores items on disk"""

import tempfile
from typing import Optional, Union, Type

from pydantic import BaseModel

from fixpoint._constants import (
    DEFAULT_DISK_CACHE_SIZE_LIMIT_BYTES as DEFAULT_SIZE_LIMIT_BYTES,
)
from fixpoint.completions import ChatCompletion
from .protocol import SupportsChatCompletionCache, CreateChatCompletionRequest
from ._shared import logger, BM
from ._genericcache.disktlru import DiskTLRUCache


# Pydantic models do not pickle well, so make a class that serializes and
# deserializes the ChatCompletion
class ChatCompletionDiskTLRUCache(
    DiskTLRUCache[CreateChatCompletionRequest[BaseModel], ChatCompletion[BaseModel]],
    SupportsChatCompletionCache,
):
    """A TLRU cache that stores chat completions on disk"""

    @classmethod
    def from_tmpdir(
        cls, ttl_s: float, size_limit_bytes: int = DEFAULT_SIZE_LIMIT_BYTES
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
