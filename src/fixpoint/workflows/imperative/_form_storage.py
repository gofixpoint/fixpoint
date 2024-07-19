"""Form storage for workflows"""

__all__ = ["FormStorage", "SupabaseFormStorage"]

from typing import List, Optional, Protocol

from pydantic import BaseModel

from fixpoint._storage import SupportsStorage
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
