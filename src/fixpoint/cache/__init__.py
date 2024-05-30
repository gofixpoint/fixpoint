"""Caching of LLM inferences"""

from typing import List

from ..completions import ChatCompletion, ChatCompletionMessageParam
from .protocol import SupportsCache
from .tlru import TLRUCache
from .disktlru import DiskTLRUCache

ChatCompletionCache = SupportsCache[List[ChatCompletionMessageParam], ChatCompletion]

__all__ = ["SupportsCache", "TLRUCache", "DiskTLRUCache", "ChatCompletionCache"]
