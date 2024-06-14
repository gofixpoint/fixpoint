"""Protocol for the storage"""

from typing import (
    Any,
    Optional,
    Dict,
    List,
    TypeVar,
    Union,
    Protocol,
    runtime_checkable,
)

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
    ) -> Union[V, None]:
        """Fetch item from storage that matches the id"""

    def fetch_with_conditions(self, conditions: dict[str, Any]) -> List[V]:
        """Fetch items from storage based on arbitrary conditions"""

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


V_co = TypeVar("V_co", covariant=True)  # Value type


@runtime_checkable
class SupportsSerialization(Protocol[V_co]):
    """Protocol for Supabase storage serialization"""

    def serialize(self) -> dict[str, Any]:
        """Method to get the serialized data of the item"""

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> V_co:
        """Method to get the deserialized data of the item"""
