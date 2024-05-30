"""Protocol for the storage"""

from typing import Any, Optional, Protocol, Dict, List, TypeVar

V = TypeVar("V")  # Value type


class SupportsStorage(Protocol[V]):
    """Protocol for the storage"""

    def fetch_latest(
        self,
        n: Optional[int] = None,
    ) -> List[V]:
        """Fetch the latest n items from the storage"""

    def fetch(
        self,
        resource_id: Any,
    ) -> V:
        """Fetch item from storage that matches the id"""

    def insert(self, data: V) -> V:
        """Insert a data item to storage"""

    def update(
        self,
        data: V,
    ) -> V:
        """Update a data item in storage"""

    def delete(
        self,
        resource_id: Any,
    ) -> None:
        """Delete a data item from storage matching id"""


class SupportsToDict(Protocol):
    """Protocol for the storage"""

    def to_dict(self) -> Dict[str, Any]:
        """Method to convert object to dictionary format."""
