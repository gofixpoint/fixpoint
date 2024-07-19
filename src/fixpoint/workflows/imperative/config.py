"""Configuration for imperative workflows

Configuration for imperative workflows, such as setting up storage.
"""

from dataclasses import dataclass
import os
from typing import Callable, List, Optional

from pydantic import BaseModel

from fixpoint import cache, memory, _storage
from fixpoint.utils.storage import new_sqlite_conn
from fixpoint._constants import DEFAULT_DISK_CACHE_SIZE_LIMIT_BYTES
from ._doc_storage import DocStorage, SupabaseDocStorage, OnDiskDocStorage
from ._form_storage import FormStorage, SupabaseFormStorage, OnDiskFormStorage
from .document import Document
from .form import Form

DEF_CHAT_CACHE_MAX_SIZE = 50000
DEF_CHAT_CACHE_TTL_S = 60 * 60 * 24 * 7


@dataclass
class StorageConfig:
    """Storage configuration for imperative workflows and its agents, etc."""

    forms_storage: Optional[FormStorage]
    docs_storage: Optional[DocStorage]
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

        # pylint: disable=unused-argument
        def memory_factory(agent_id: str) -> memory.SupportsMemory:
            """create memory collections per agent"""
            return memory.SupabaseMemory(
                supabase_url=supabase_url,
                supabase_api_key=supabase_api_key,
            )

        return cls(
            forms_storage=forms_storage,
            docs_storage=docs_storage,
            agent_cache=agent_cache,
            memory_factory=memory_factory,
        )

    @classmethod
    def with_disk(
        cls,
        *,
        storage_path: str,
        agent_cache_ttl_s: int,
        agent_cache_size_limit_bytes: int = DEFAULT_DISK_CACHE_SIZE_LIMIT_BYTES,
    ) -> "StorageConfig":
        """Configure disk storage"""

        agent_cache_dir = os.path.join(storage_path, "agent_cache")
        sqlite_conn = new_sqlite_conn(os.path.join(storage_path, "db.sqlite"))
        mem_conn = sqlite_conn
        doc_conn = sqlite_conn
        form_conn = sqlite_conn

        # TODO(dbmikus) support on-disk memory storage
        # https://linear.app/fixpoint/issue/PRO-41/add-on-disk-memory-storage
        def memory_factory(_agent_id: str) -> memory.SupportsMemory:
            """create memory collections per agent"""
            return memory.OnDiskMemory(conn=mem_conn)

        agent_cache = cache.ChatCompletionDiskTLRUCache(
            cache_dir=agent_cache_dir,
            ttl_s=agent_cache_ttl_s,
            size_limit_bytes=agent_cache_size_limit_bytes,
        )

        return cls(
            # TODO(dbmikus) support on-disk storage for forms and docs
            # https://linear.app/fixpoint/issue/PRO-40/add-on-disk-step-and-task-storage-for-workflows
            forms_storage=OnDiskFormStorage(form_conn),
            docs_storage=OnDiskDocStorage(doc_conn),
            agent_cache=agent_cache,
            memory_factory=memory_factory,
        )

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
) -> FormStorage:
    """Create a supabase storage driver for forms"""
    supabase_storage = _storage.SupabaseStorage[Form[BaseModel]](
        url=supabase_url,
        key=supabase_api_key,
        table="forms_with_metadata",
        order_key="id",
        id_column="id",
        value_type=Form[BaseModel],
    )
    return SupabaseFormStorage(supabase_storage)


def create_docs_supabase_storage(
    supabase_url: str, supabase_api_key: str
) -> DocStorage:
    """Create a supabase storage driver for documents"""
    supabase_storage = _storage.SupabaseStorage[Document](
        url=supabase_url,
        key=supabase_api_key,
        table="documents",
        order_key="id",
        id_column="id",
        value_type=Document,
    )
    return SupabaseDocStorage(supabase_storage)


def create_chat_completion_cache_supabase_storage(
    supabase_url: str, supabase_api_key: str
) -> _storage.SupabaseStorage[cache.ChatCompletionTLRUCacheItem[BaseModel]]:
    """Create a supabase storage driver for chat completion caching"""
    return _storage.SupabaseStorage(
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
) -> _storage.SupabaseStorage[cache.TLRUCacheItem[str]]:
    """Create a supabase storage driver for chat completion caching"""
    return _storage.SupabaseStorage(
        url=supabase_url,
        key=supabase_api_key,
        table="completion_cache",
        order_key="expires_at",
        id_column="key",
        value_type=cache.TLRUCacheItem[str],
    )


def _create_memory_supabase_storage(
    supabase_url: str,
    supabase_api_key: str,
    agent_id: str,  # pylint: disable=unused-argument
) -> _storage.SupabaseStorage[memory.MemoryItem]:
    """Create a supabase storage driver for agent memories"""
    # TODO(dbmikus) we need to make use of the agent_id
    # We put a id on the agent itself, so do we need an agent_id on the memory?
    # We can either attach agent IDs to the agents or to the memory, or perhaps
    # to both.

    return _storage.SupabaseStorage[memory.MemoryItem](
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
