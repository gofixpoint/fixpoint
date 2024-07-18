"""Memory storage protocol and implementations."""

__all__ = ["MemoryStorage", "OnDiskMemoryStorage", "SupabaseMemoryStorage"]

import base64
from dataclasses import dataclass
import datetime
import json
import sqlite3
from typing import Any, List, Protocol, Optional, TypedDict

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


# typed dict for cursor
class _Cursor(TypedDict):
    id: str
    created_at: datetime.datetime


class OnDiskMemoryStorage(MemoryStorage):
    """Store memories on disk"""

    _conn: sqlite3.Connection

    def __init__(
        self,
        conn: sqlite3.Connection,
    ) -> None:
        self._conn = conn
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    workflow_id TEXT,
                    workflow_run_id TEXT,
                    messages TEXT,
                    completion TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def insert(self, memory: MemoryItem) -> None:
        """Insert a memory into the storage"""
        with self._conn:
            self._conn.execute(
                # pylint: disable=line-too-long
                """
                INSERT INTO memories
                    (id, agent_id, workflow_id, workflow_run_id, messages, completion, created_at)
                VALUES (:id, :agent_id, :workflow_id, :workflow_run_id, :messages, :completion, :created_at)
                """,
                memory.serialize(),
            )

    def list(self, cursor: Optional[str] = None, n: int = 100) -> _ListResponse:
        """Get the list of memories"""
        cursor_obj = self._parse_cursor(cursor) if cursor else None
        with self._conn:
            if cursor_obj:
                dbcursor = self._conn.execute(
                    # pylint: disable=line-too-long
                    """
                    SELECT id, agent_id, workflow_id, workflow_run_id, messages, completion, created_at
                    FROM memories
                    WHERE created_at < :created_at OR (created_at = :created_at AND id > :id)
                    ORDER BY created_at DESC, id ASC
                    LIMIT :n
                    """,
                    {
                        "n": n,
                        # pylint: disable=unsubscriptable-object
                        "created_at": cursor_obj["created_at"].isoformat(),
                        # pylint: disable=unsubscriptable-object
                        "id": cursor_obj["id"],
                    },
                )
            else:
                dbcursor = self._conn.execute(
                    # pylint: disable=line-too-long
                    """
                    SELECT id, agent_id, workflow_id, workflow_run_id, messages, completion, created_at
                    FROM memories
                    ORDER BY created_at DESC, id ASC
                    LIMIT :n
                    """,
                    {"n": n},
                )
            mems: List[MemoryItem] = []
            for row in dbcursor.fetchall():
                mems.append(self._load_row(row))
            return _ListResponse(
                memories=mems,
                next_cursor=self._format_cursor(mems) if len(mems) == n else None,
            )

    def get(self, mem_id: str) -> Optional[MemoryItem]:
        """Get a memory item by ID"""
        with self._conn:
            dbcursor = self._conn.execute(
                """
                SELECT id, agent_id, workflow_id, workflow_run_id, messages, completion, created_at
                FROM memories
                WHERE id = :id
                """,
                {"id": mem_id},
            )
            row = dbcursor.fetchone()
            if row:
                return self._load_row(row)
            return None

    def _load_row(self, row: Any) -> MemoryItem:
        row_dict = {
            "id": row[0],
            "agent_id": row[1],
            "workflow_id": row[2],
            "workflow_run_id": row[3],
            "messages": row[4],
            "completion": row[5],
            "created_at": row[6],
        }
        return MemoryItem.deserialize(row_dict)

    def _format_cursor(self, memories: List[MemoryItem]) -> str:
        last_mem = memories[-1]
        return base64.urlsafe_b64encode(
            json.dumps(
                {"id": last_mem.id, "created_at": last_mem.created_at.isoformat()}
            ).encode()
        ).decode()

    def _parse_cursor(self, cursor: str) -> _Cursor:
        d = json.loads(base64.urlsafe_b64decode(cursor).decode())
        return {
            "id": d["id"],
            "created_at": datetime.datetime.fromisoformat(d["created_at"]),
        }


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
