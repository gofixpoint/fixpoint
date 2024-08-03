"""Document storage for workflows"""

__all__ = ["DocStorage", "SupabaseDocStorage"]

import json
import sqlite3
from typing import Any, Dict, List, Optional, Protocol

from fixpoint._storage import SupportsStorage, definitions as storage_definitions
from fixpoint._storage.sql import format_where_clause
from .document import Document


class DocStorage(Protocol):
    """Document storage for workflows"""

    # pylint: disable=redefined-builtin
    def get(self, id: str) -> Optional[Document]:
        """Get the given document"""

    def create(self, document: Document) -> None:
        """Create a new document"""

    def update(self, document: Document) -> None:
        """Update an existing document"""

    def list(
        self, path: Optional[str] = None, workflow_run_id: Optional[str] = None
    ) -> List[Document]:
        """List all documents

        If path is provided, list documents in the given path.
        """


class SupabaseDocStorage(DocStorage):
    """Supabase document storage for workflows"""

    _storage: SupportsStorage[Document]

    def __init__(self, storage: SupportsStorage[Document]):
        self._storage = storage

    # pylint: disable=redefined-builtin
    def get(self, id: str) -> Optional[Document]:
        return self._storage.fetch(id)

    def create(self, document: Document) -> None:
        self._storage.insert(document)

    def update(self, document: Document) -> None:
        self._storage.update(document)

    def list(
        self, path: Optional[str] = None, workflow_run_id: Optional[str] = None
    ) -> List[Document]:
        conditions = {"workflow_run_id": workflow_run_id}
        if path:
            conditions["path"] = path
        return self._storage.fetch_with_conditions(conditions)


class OnDiskDocStorage(DocStorage):
    """On-disk document storage for workflows"""

    _conn: sqlite3.Connection

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        with self._conn:
            self._conn.execute(storage_definitions.DOCS_SQLITE_TABLE)

    # pylint: disable=redefined-builtin
    def get(self, id: str) -> Optional[Document]:
        with self._conn:
            dbcursor = self._conn.execute(
                """
                SELECT
                    id,
                    workflow_id,
                    workflow_run_id,
                    path,
                    metadata,
                    contents,
                    task,
                    step,
                    versions
                FROM documents WHERE id = :id
                """,
                {"id": id},
            )
            row = dbcursor.fetchone()
            if not row:
                return None
            return self._load_row(row)

    def create(self, document: Document) -> None:
        mdict = document.model_dump()
        mdict["metadata"] = json.dumps(mdict["metadata"])
        mdict["versions"] = json.dumps(mdict["versions"])
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO documents (
                    id,
                    workflow_id,
                    workflow_run_id,
                    path,
                    metadata,
                    contents,
                    task,
                    step,
                    versions
                )
                VALUES (
                    :id,
                    :workflow_id,
                    :workflow_run_id,
                    :path,
                    :metadata,
                    :contents,
                    :task,
                    :step,
                    :versions
                )
                """,
                mdict,
            )

    def update(self, document: Document) -> None:
        doc_dict = {
            "id": document.id,
            "metadata": json.dumps(document.metadata),
            "contents": document.contents,
        }
        with self._conn:
            self._conn.execute(
                """
                UPDATE documents SET
                    metadata = :metadata,
                    contents = :contents
                WHERE id = :id
                """,
                doc_dict,
            )

    def list(
        self, path: Optional[str] = None, workflow_run_id: Optional[str] = None
    ) -> List[Document]:
        params: Dict[str, Any] = {}
        where_clause = ""
        if path:
            params["path"] = path
        if workflow_run_id:
            params["workflow_run_id"] = workflow_run_id
        if params:
            where_clause = format_where_clause(params)

        with self._conn:
            dbcursor = self._conn.execute(
                f"""
                SELECT
                    id,
                    workflow_id,
                    workflow_run_id,
                    path,
                    metadata,
                    contents,
                    task,
                    step,
                    versions
                FROM documents
                {where_clause}
                """,
                params,
            )
            return [self._load_row(row) for row in dbcursor]

    def _load_row(self, row: Any) -> Document:
        return Document(
            id=row[0],
            workflow_id=row[1],
            workflow_run_id=row[2],
            path=row[3],
            metadata=json.loads(row[4]),
            contents=row[5],
            versions=json.loads(row[8]),
        )
