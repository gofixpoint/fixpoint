"""Document storage for workflows"""

__all__ = ["DocStorage", "SupabaseDocStorage", "OnDiskDocStorage"]

import json
import sqlite3
from typing import Any, Dict, List, Optional, Protocol

from fixpoint._storage import SupportsStorage, definitions as storage_definitions
from fixpoint._storage.sql import format_where_clause
from .document import Document


_NULL_COL_ID = "__null__"


class DocStorage(Protocol):
    """Document storage for workflows"""

    # pylint: disable=redefined-builtin
    def get(
        self,
        id: str,
        workflow_id: Optional[str] = None,
        workflow_run_id: Optional[str] = None,
    ) -> Optional[Document]:
        """Get the given document"""

    def create(self, document: Document) -> None:
        """Create a new document"""

    def update(self, document: Document) -> None:
        """Update an existing document"""

    def list(
        self,
        path: Optional[str] = None,
        workflow_id: Optional[str] = None,
        workflow_run_id: Optional[str] = None,
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
    def get(
        self,
        id: str,
        workflow_id: Optional[str] = None,
        workflow_run_id: Optional[str] = None,
    ) -> Optional[Document]:
        doc_res = self._storage.fetch(
            self._transform_id(id, workflow_id, workflow_run_id)
        )
        if doc_res is None:
            return None
        return _transform_fetched_supabase_doc(doc_res)

    def create(self, document: Document) -> None:
        document = _fix_doc_ids(document)
        document.id = self._transform_id(
            document.id, document.workflow_id, document.workflow_run_id
        )
        self._storage.insert(document)

    def update(self, document: Document) -> None:
        document = _fix_doc_ids(document)
        document.id = self._transform_id(
            document.id, document.workflow_id, document.workflow_run_id
        )
        self._storage.update(document)

    def list(
        self,
        path: Optional[str] = None,
        workflow_id: Optional[str] = None,
        workflow_run_id: Optional[str] = None,
    ) -> List[Document]:
        conditions: Dict[str, str] = {}
        if workflow_id:
            conditions["workflow_id"] = workflow_id
        if workflow_run_id:
            conditions["workflow_run_id"] = workflow_run_id
        if path:
            conditions["path"] = path
        docs_list = self._storage.fetch_with_conditions(conditions)
        return [_transform_fetched_supabase_doc(doc) for doc in docs_list]

    def _transform_id(
        self,
        id: str,
        workflow_id: Optional[str] = None,
        workflow_run_id: Optional[str] = None,
    ) -> str:
        if workflow_id is None:
            workflow_id = _NULL_COL_ID
        if workflow_run_id is None:
            workflow_run_id = _NULL_COL_ID
        return f"{workflow_id}/{workflow_run_id}/{id}"


class OnDiskDocStorage(DocStorage):
    """On-disk document storage for workflows"""

    _conn: sqlite3.Connection

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        with self._conn:
            self._conn.execute(storage_definitions.DOCS_SQLITE_TABLE)

    # pylint: disable=redefined-builtin
    def get(
        self,
        id: str,
        workflow_id: Optional[str] = None,
        workflow_run_id: Optional[str] = None,
    ) -> Optional[Document]:
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
                FROM documents WHERE
                    id = :id
                    AND workflow_id = :workflow_id
                    AND workflow_run_id = :workflow_run_id
                """,
                {
                    "id": id,
                    "workflow_id": workflow_id or _NULL_COL_ID,
                    "workflow_run_id": workflow_run_id or _NULL_COL_ID,
                },
            )
            row = dbcursor.fetchone()
            if not row:
                return None
            return self._load_row(row)

    def create(self, document: Document) -> None:
        document = _fix_doc_ids(document)
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
            "workflow_id": document.workflow_id or _NULL_COL_ID,
            "workflow_run_id": document.workflow_run_id or _NULL_COL_ID,
            "metadata": json.dumps(document.metadata),
            "contents": document.contents,
        }
        with self._conn:
            self._conn.execute(
                """
                UPDATE documents SET
                    metadata = :metadata,
                    contents = :contents
                WHERE
                    id = :id
                    AND workflow_id = :workflow_id
                    AND workflow_run_id = :workflow_run_id
                """,
                doc_dict,
            )

    def list(
        self,
        path: Optional[str] = None,
        workflow_id: Optional[str] = None,
        workflow_run_id: Optional[str] = None,
    ) -> List[Document]:
        params: Dict[str, Any] = {}
        where_clause = ""
        if path:
            params["path"] = path
        if workflow_id:
            params["workflow_id"] = workflow_id
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
        wid = row[1]
        if wid == _NULL_COL_ID:
            wid = None
        wrid = row[2]
        if wrid == _NULL_COL_ID:
            wrid = None

        return Document(
            id=row[0],
            workflow_id=wid,
            workflow_run_id=wrid,
            path=row[3],
            metadata=json.loads(row[4]),
            contents=row[5],
            versions=json.loads(row[8]),
        )


def _fix_doc_ids(doc: Document) -> Document:
    doc = doc.model_copy(deep=True)
    if doc.workflow_id is None:
        doc.workflow_id = _NULL_COL_ID
    if doc.workflow_run_id is None:
        doc.workflow_run_id = _NULL_COL_ID
    return doc


def _transform_fetched_supabase_doc(doc: Document) -> Document:
    if doc.workflow_id == _NULL_COL_ID:
        doc.workflow_id = None
    if doc.workflow_run_id == _NULL_COL_ID:
        doc.workflow_run_id = None
    doc.id = doc.id.split("/")[-1]
    return doc
