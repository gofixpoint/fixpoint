"""Memory storage protocol and implementations."""

__all__ = ["MemoryStorage", "OnDiskMemoryStorage"]

from dataclasses import dataclass
from typing import List, Protocol, Optional

import diskcache

from fixpoint._storage import SupabaseStorage
from .protocol import MemoryItem


@dataclass
class _ListResponse:
    """A list memories response"""

    memories: List[MemoryItem]
    next_cursor: Optional[str] = None


class MemoryStorage(Protocol):
    """Protocol for storing memories"""

    def insert(self, memory: MemoryItem) -> None:
        """Insert a memory into the storage"""

    def list(self, cursor: Optional[str] = None) -> _ListResponse:
        """Get the list of memories"""

    def get(self, mem_id: str) -> Optional[MemoryItem]:
        """Get a memory item by ID"""


class OnDiskMemoryStorage(MemoryStorage):
    """Store memories on disk"""

    _cache: diskcache.Cache

    def __init__(
        self,
        cache: diskcache.Cache,
    ) -> None:
        self._cache = cache

    def insert(self, memory: MemoryItem) -> None:
        """Insert a memory into the storage"""
        raise NotImplementedError()

    def list(self, cursor: Optional[str] = None) -> _ListResponse:
        """Get the list of memories"""
        raise NotImplementedError()

    def get(self, mem_id: str) -> Optional[MemoryItem]:
        """Get a memory item by ID"""
        raise NotImplementedError()


class SupabaseMemoryStorage(MemoryStorage):
    """Store memories in Supabase"""

    _storage: SupabaseStorage[MemoryItem]
    _agent_id: str

    def __init__(
        self,
        supabase_url: str,
        supabase_api_key: str,
    ) -> None:
        self._storage = SupabaseStorage(
            url=supabase_url,
            key=supabase_api_key,
            table="memory_store",
            # TODO(dbmikus) what should we do about composite ID columns?
            # Personally, I think we should not use the generic SupabaseStorage
            # class for storing agent memories, and instead pass in an interface
            # that is resource-oriented around these memories
            order_key="agent_id",
            id_column="id",
            value_type=MemoryItem,
        )

    def insert(self, memory: MemoryItem) -> None:
        """Insert a memory into the storage"""
        self._storage.insert(memory)

    def list(self, cursor: Optional[str] = None) -> _ListResponse:
        """Get the list of memories"""
        # TODO(dbmikus) support paginating through memories
        entries = self._storage.fetch_latest()
        return _ListResponse(memories=entries, next_cursor=None)

    def get(self, mem_id: str) -> Optional[MemoryItem]:
        """Get a memory item by ID"""
        return self._storage.fetch(mem_id)
