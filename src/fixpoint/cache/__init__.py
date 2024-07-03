"""Caching of LLM inferences"""

from typing import List

from .protocol import (
    SupportsCache,
    SupportsChatCompletionCache,
    CreateChatCompletionRequest,
)
from ._shared import parse_create_chat_completion_request
from ._genericcache.tlru import TLRUCacheItem
from .tlru import ChatCompletionTLRUCache, ChatCompletionTLRUCacheItem
from .disktlru import ChatCompletionDiskTLRUCache

__all__ = [
    "ChatCompletionDiskTLRUCache",
    "ChatCompletionTLRUCache",
    "ChatCompletionTLRUCacheItem",
    "CreateChatCompletionRequest",
    "parse_create_chat_completion_request",
    "SupportsCache",
    "SupportsChatCompletionCache",
    "TLRUCacheItem",
]
