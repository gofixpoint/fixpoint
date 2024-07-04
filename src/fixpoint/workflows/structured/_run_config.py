"""Configuration for running workflows."""

from dataclasses import dataclass

from ..imperative import StorageConfig
from ..imperative.config import (
    DEF_CHAT_CACHE_MAX_SIZE,
    DEF_CHAT_CACHE_TTL_S,
)
from ._callcache import CallCache, StepInMemCallCache, TaskInMemCallCache


@dataclass
class CallCacheConfig:
    """Configuration for task and step call caches."""

    steps: CallCache
    tasks: CallCache


@dataclass
class RunConfig:
    """Configuration for running workflows.

    Configuration for running workflows, such as the storage backends to use.
    """

    storage: StorageConfig
    call_cache: CallCacheConfig

    @classmethod
    def with_defaults(
        cls,
        chat_cache_maxsize: int = DEF_CHAT_CACHE_MAX_SIZE,
        chat_cache_ttl_s: int = DEF_CHAT_CACHE_TTL_S,
    ) -> "RunConfig":
        """Configure run for default backend"""
        return cls.with_in_memory(chat_cache_maxsize, chat_cache_ttl_s)

    @classmethod
    def with_supabase(
        cls,
        supabase_url: str,
        supabase_api_key: str,
        chat_cache_maxsize: int = DEF_CHAT_CACHE_MAX_SIZE,
        chat_cache_ttl_s: int = DEF_CHAT_CACHE_TTL_S,
    ) -> "RunConfig":
        """Configure run for Supabase backend"""
        storage = StorageConfig.with_supabase(
            supabase_url, supabase_api_key, chat_cache_maxsize, chat_cache_ttl_s
        )
        # TODO(dbmikus) support Supabase storage
        call_cache = CallCacheConfig(
            steps=StepInMemCallCache(),
            tasks=TaskInMemCallCache(),
        )
        return cls(storage, call_cache)

    @classmethod
    def with_disk(cls) -> "RunConfig":
        """Configure run for disk storage"""
        raise NotImplementedError()

    @classmethod
    def with_in_memory(
        cls,
        chat_cache_maxsize: int = DEF_CHAT_CACHE_MAX_SIZE,
        chat_cache_ttl_s: int = DEF_CHAT_CACHE_TTL_S,
    ) -> "RunConfig":
        """Configure run for in-memory storage"""
        storage = StorageConfig.with_in_memory(chat_cache_maxsize, chat_cache_ttl_s)
        call_cache = CallCacheConfig(
            steps=StepInMemCallCache(),
            tasks=TaskInMemCallCache(),
        )
        return cls(storage, call_cache)
