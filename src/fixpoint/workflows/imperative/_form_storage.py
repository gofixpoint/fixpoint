"""Form storage for workflows"""

__all__ = ["FormStorage", "SupabaseFormStorage"]

import json
import sqlite3
from typing import Any, Dict, List, Optional, Protocol

from pydantic import BaseModel

from fixpoint._storage import SupportsStorage
from fixpoint._storage.sql import format_where_clause
from .form import Form


class FormStorage(Protocol):
    """Form storage for workflows"""

    # pylint: disable=redefined-builtin
    def get(self, id: str) -> Optional[Form[BaseModel]]:
        """Get the given Form"""

    def create(self, form: Form[BaseModel]) -> None:
        """Create a new Form"""

    def update(self, form: Form[BaseModel]) -> None:
        """Update an existing Form"""

    def list(
        self, path: Optional[str] = None, workflow_run_id: Optional[str] = None
    ) -> List[Form[BaseModel]]:
        """List all Forms

        If path is provided, list Forms in the given path.
        """


class SupabaseFormStorage(FormStorage):
    """Supabase form storage for workflows"""

    _storage: SupportsStorage[Form[BaseModel]]

    def __init__(self, storage: SupportsStorage[Form[BaseModel]]):
        self._storage = storage

    # pylint: disable=redefined-builtin
    def get(self, id: str) -> Optional[Form[BaseModel]]:
        return self._storage.fetch(id)

    def create(self, form: Form[BaseModel]) -> None:
        self._storage.insert(form)

    def update(self, form: Form[BaseModel]) -> None:
        self._storage.update(form)

    def list(
        self, path: Optional[str] = None, workflow_run_id: Optional[str] = None
    ) -> List[Form[BaseModel]]:
        conditions = {"workflow_run_id": workflow_run_id}
        if path:
            conditions["path"] = path
        return self._storage.fetch_with_conditions(conditions)


class OnDiskFormStorage(FormStorage):
    """On-disk form storage for workflows"""

    _conn: sqlite3.Connection

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS forms_with_metadata (
                    id text PRIMARY KEY,
                    workflow_id text,
                    workflow_run_id text,
                    metadata jsonb,
                    path text NOT NULL,
                    contents jsonb NOT NULL,
                    form_schema text NOT NULL,
                    versions jsonb,
                    task text,
                    step text
                );
                """
            )

    # pylint: disable=redefined-builtin
    def get(self, id: str) -> Optional[Form[BaseModel]]:
        with self._conn:
            dbcursor = self._conn.execute(
                """
                SELECT
                    id,
                    workflow_id,
                    workflow_run_id,
                    metadata,
                    path,
                    contents,
                    form_schema,
                    versions,
                    task,
                    step
                FROM forms_with_metadata
                WHERE id = :id
                """,
                {"id": id},
            )
            row = dbcursor.fetchone()
            if not row:
                return None
            return self._load_row(row)

    def create(self, form: Form[BaseModel]) -> None:
        fdict = form.serialize()
        fdict["metadata"] = json.dumps(fdict["metadata"])
        fdict["contents"] = json.dumps(fdict["contents"])
        fdict["form_schema"] = json.dumps(fdict["form_schema"])
        fdict["versions"] = json.dumps(fdict["versions"])

        with self._conn:
            self._conn.execute(
                """
                INSERT INTO forms_with_metadata (
                    id,
                    workflow_id,
                    workflow_run_id,
                    metadata,
                    path,
                    contents,
                    form_schema,
                    versions,
                    task,
                    step
                ) VALUES (
                    :id,
                    :workflow_id,
                    :workflow_run_id,
                    :metadata,
                    :path,
                    :contents,
                    :form_schema,
                    :versions,
                    :task,
                    :step
                )
                """,
                fdict,
            )

    def update(self, form: Form[BaseModel]) -> None:
        form_dict = {
            "id": form.id,
            "metadata": json.dumps(form.metadata),
            "contents": form.contents.model_dump_json(),
        }
        with self._conn:
            self._conn.execute(
                """
                UPDATE forms_with_metadata
                SET metadata = :metadata,
                    contents = :contents
                WHERE id = :id
                """,
                form_dict,
            )

    def list(
        self, path: Optional[str] = None, workflow_run_id: Optional[str] = None
    ) -> List[Form[BaseModel]]:
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
                SELECT * FROM forms_with_metadata
                {where_clause}
                """,
                params,
            )
            return [self._load_row(row) for row in dbcursor]

    def _load_row(self, row: Any) -> Form[BaseModel]:
        return Form.deserialize(
            {
                "id": row[0],
                "workflow_id": row[1],
                "workflow_run_id": row[2],
                "metadata": json.loads(row[3]),
                "path": row[4],
                "contents": json.loads(row[5]),
                "form_schema": json.loads(row[6]),
                "versions": json.loads(row[7]),
                "task": row[8],
                "step": row[9],
            }
        )
