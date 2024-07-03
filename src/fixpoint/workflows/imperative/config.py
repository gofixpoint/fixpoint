"""Configuration for imperative workflows

Configuration for imperative workflows, such as setting up storage.
"""

from dataclasses import dataclass
from typing import Callable, List, Optional

from pydantic import BaseModel

from fixpoint import cache, memory, storage
from .document import Document
from .form import Form

DEF_CHAT_CACHE_MAX_SIZE = 50000
DEF_CHAT_CACHE_TTL_S = 60 * 60 * 24 * 7


@dataclass
class StorageConfig:
    """Storage configuration for imperative workflows and its agents, etc."""

    forms_storage: Optional[storage.SupportsStorage[Form[BaseModel]]]
    docs_storage: Optional[storage.SupportsStorage[Document]]
    agent_cache: Optional[cache.SupportsChatCompletionCache]
    memory_factory: Callable[[str], memory.SupportsMemory]

    @classmethod
    def with_defaults(
        cls,
        chat_cache_maxsize: int = DEF_CHAT_CACHE_MAX_SIZE,
        chat_cache_ttl_s: int = DEF_CHAT_CACHE_TTL_S,
    ) -> "StorageConfig":
        """Configure default storage"""
        return cls.with_in_memory(chat_cache_maxsize, chat_cache_ttl_s)

    @classmethod
    def with_supabase(
        cls,
        supabase_url: str,
        supabase_api_key: str,
        chat_cache_maxsize: int = DEF_CHAT_CACHE_MAX_SIZE,
        chat_cache_ttl_s: int = DEF_CHAT_CACHE_TTL_S,
    ) -> "StorageConfig":
        """Configure supabase storage"""
        forms_storage = create_form_supabase_storage(supabase_url, supabase_api_key)
        docs_storage = create_docs_supabase_storage(supabase_url, supabase_api_key)
        agent_cache = cache.ChatCompletionTLRUCache(
            maxsize=chat_cache_maxsize,
            ttl_s=chat_cache_ttl_s,
            storage=create_chat_completion_cache_supabase_storage(
                supabase_url, supabase_api_key
            ),
        )

        def memory_factory(agent_id: str) -> memory.SupportsMemory:
            """create memory collections per agent"""
            return memory.Memory(
                storage=create_memory_supabase_storage(
                    supabase_url, supabase_api_key, agent_id
                ),
            )

        return cls(
            forms_storage=forms_storage,
            docs_storage=docs_storage,
            agent_cache=agent_cache,
            memory_factory=memory_factory,
        )

    @classmethod
    def with_disk(cls) -> "StorageConfig":
        """Configure disk storage"""
        raise NotImplementedError()

    @classmethod
    def with_in_memory(
        cls,
        chat_cache_maxsize: int = DEF_CHAT_CACHE_MAX_SIZE,
        chat_cache_ttl_s: int = DEF_CHAT_CACHE_TTL_S,
    ) -> "StorageConfig":
        """Configure in-memory storage"""

        def memory_factory(_agent_id: str) -> memory.SupportsMemory:
            """create memory collections per agent"""
            return memory.Memory()

        agent_cache = cache.ChatCompletionTLRUCache(
            maxsize=chat_cache_maxsize,
            ttl_s=chat_cache_ttl_s,
        )

        return cls(
            forms_storage=None,
            docs_storage=None,
            agent_cache=agent_cache,
            memory_factory=memory_factory,
        )


_def_storage: List[Optional[StorageConfig]] = [None]


def get_default_storage_config() -> StorageConfig:
    """Gets the default storage config singleton"""
    if _def_storage[0] is None:
        storage_cfg = StorageConfig.with_defaults(
            chat_cache_maxsize=DEF_CHAT_CACHE_MAX_SIZE,
            chat_cache_ttl_s=DEF_CHAT_CACHE_TTL_S,
        )
        _def_storage[0] = storage_cfg
        return storage_cfg
    else:
        return _def_storage[0]


def create_form_supabase_storage(
    supabase_url: str, supabase_api_key: str
) -> storage.SupabaseStorage[Form[BaseModel]]:
    """Create a supabase storage driver for forms"""
    return storage.SupabaseStorage[Form[BaseModel]](
        url=supabase_url,
        key=supabase_api_key,
        table="forms_with_metadata",
        order_key="id",
        id_column="id",
        value_type=Form[BaseModel],
    )


def create_docs_supabase_storage(
    supabase_url: str, supabase_api_key: str
) -> storage.SupabaseStorage[Document]:
    """Create a supabase storage driver for documents"""
    return storage.SupabaseStorage[Document](
        url=supabase_url,
        key=supabase_api_key,
        table="documents",
        order_key="id",
        id_column="id",
        value_type=Document,
    )


def create_chat_completion_cache_supabase_storage(
    supabase_url: str, supabase_api_key: str
) -> storage.SupabaseStorage[cache.ChatCompletionTLRUCacheItem[BaseModel]]:
    """Create a supabase storage driver for chat completion caching"""
    return storage.SupabaseStorage(
        url=supabase_url,
        key=supabase_api_key,
        table="completion_cache",
        order_key="expires_at",
        id_column="key",
        # We cannot not specify the generic type parameter for
        # TLRUCacheItem, because then when we try to do `isinstance(cls,
        # type)`, the class will actually be a `typing.GenericAlias` and not
        # a type (class definition).
        value_type=cache.ChatCompletionTLRUCacheItem,
    )


def create_str_cache_supabase_storage(
    supabase_url: str, supabase_api_key: str
) -> storage.SupabaseStorage[cache.TLRUCacheItem[str]]:
    """Create a supabase storage driver for chat completion caching"""
    return storage.SupabaseStorage(
        url=supabase_url,
        key=supabase_api_key,
        table="completion_cache",
        order_key="expires_at",
        id_column="key",
        value_type=cache.TLRUCacheItem[str],
    )


def create_memory_supabase_storage(
    supabase_url: str,
    supabase_api_key: str,
    agent_id: str,  # pylint: disable=unused-argument
) -> storage.SupabaseStorage[memory.MemoryItem]:
    """Create a supabase storage driver for agent memories"""
    # TODO(dbmikus) we need to make use of the agent_id
    # We put a id on the agent itself, so do we need an agent_id on the memory?
    # We can either attach agent IDs to the agents or to the memory, or perhaps
    # to both.

    return storage.SupabaseStorage[memory.MemoryItem](
        url=supabase_url,
        key=supabase_api_key,
        table="memory_store",
        # TODO(dbmikus) what should we do about composite ID columns?
        # Personally, I think we should not use the generic SupabaseStorage
        # class for storing agent memories, and instead pass in an interface
        # that is resource-oriented around these memories
        order_key="agent_id",
        id_column="id",
        value_type=memory.MemoryItem,
    )
