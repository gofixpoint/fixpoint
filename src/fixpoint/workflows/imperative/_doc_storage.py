"""Document storage for workflows"""

__all__ = ["DocStorage", "SupabaseDocStorage"]

from typing import List, Optional, Protocol

from fixpoint._storage import SupportsStorage
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
