"""Protocol for the storage"""

from typing import Any, Optional, Protocol, Dict


class SupportsStorage(Protocol):
    """Protocol for the storage"""

    def fetch_latest(
        self,
        n: Optional[int] = None,
        resource: Optional[str] = None,
        order_key: Optional[str] = None,
        model: Optional[Any] = None,
    ) -> Any:
        """Fetch the latest n items from the storage"""

    def fetch(
        self,
        filter_criteria: Dict[str, Any],
        resource: Optional[str] = None,
        model: Optional[Any] = None,
    ) -> Any:
        """Fetch items from storage that match the lookup_options"""

    def insert(
        self, data: Any, resource: Optional[str] = None, model: Optional[Any] = None
    ) -> Any:
        """Insert a data item to a storage resource"""

    def update(
        self,
        data: Any,
        resource: Optional[str] = None,
        model: Optional[Any] = None,
    ) -> Any:
        """Update a data item in storage matching filter_criteria"""

    def delete(
        self,
        filter_criteria: Dict[str, Any],
        resource: Optional[str] = None,
    ) -> Any:
        """Delete a data item from storage matching filter_criteria"""
