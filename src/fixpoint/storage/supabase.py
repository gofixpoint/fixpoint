"""Supabase storage"""

from typing import Any, Optional, TypeVar, List, Type, Union
from postgrest import SyncRequestBuilder  # type: ignore
from supabase import create_client, Client
from .protocol import SupportsStorage, SupportsSupabaseSerialization

V = TypeVar("V", bound=SupportsSupabaseSerialization[Any])


class SupabaseStorage(SupportsStorage[V]):
    """Supabase storage"""

    _client: Client
    _table: str
    _order_key: str
    _id_column: str
    _value_type: Type[V]

    def __init__(
        self,
        url: str,
        key: str,
        table: str,
        order_key: str,
        id_column: str,
        value_type: Type[V],
    ):
        self._table = table
        self._order_key = order_key
        self._id_column = id_column
        self._value_type = value_type
        try:
            self._client: Client = create_client(url, key)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Supabase: {e}") from e

    def _query_table(self) -> SyncRequestBuilder[dict[str, Any]]:
        return self._client.table(self._table)

    def _deserialize_results(self, results: list[dict[str, Any]]) -> List[V]:
        return [self._value_type.deserialize(data=item) for item in results]

    def _pick_first(self, results: List[V]) -> V:
        """Pick the first item from the results"""
        if results:
            return results[0]
        raise ValueError("No results found")

    def _pick_first_optional(self, results: List[V]) -> Optional[V]:
        """Pick the first item from the results"""
        if results:
            return results[0]
        return None

    def fetch_latest(self, n: Optional[int] = None) -> List[V]:
        """Fetch the latest n items from the storage"""
        try:
            query = self._query_table().select("*").order(self._order_key, desc=True)
            if n:
                resp = query.limit(n).execute()
            else:
                resp = query.execute()
            return self._deserialize_results(resp.data)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch latest data: {e}") from e

    def fetch_with_conditions(self, conditions: dict[str, Any]) -> List[V]:
        """Fetch items from storage based on arbitrary conditions"""
        try:
            query = self._query_table().select("*")
            for column, value in conditions.items():
                query = query.eq(column, value)
            resp = query.execute()
            return self._deserialize_results(resp.data)
        except Exception as e:
            raise RuntimeError(
                f"Failed to fetch data with conditions {conditions}: {e}"
            ) from e

    def fetch(self, resource_id: Any) -> Union[V, None]:
        """Fetch data items from storage"""
        try:
            query = self._query_table().select("*")
            resp = query.eq(self._id_column, resource_id).execute()
            results = self._deserialize_results(resp.data)
            return self._pick_first_optional(results)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch data: {e}") from e

    def insert(self, data: V) -> V:
        """Insert data items to storage"""
        try:
            query = self._query_table()
            resp = query.insert(data.serialize()).execute()
            results = self._deserialize_results(resp.data)
            return self._pick_first(results)
        except Exception as e:
            raise RuntimeError(f"Failed to insert data: {e}") from e

    def update(
        self,
        data: V,
    ) -> V:
        """Update items in storage (uses upsert)"""
        try:
            query = self._query_table()
            resp = query.upsert(data.serialize()).execute()
            results = self._deserialize_results(resp.data)
            return self._pick_first(results)
        except Exception as e:
            raise RuntimeError(f"Failed to update data: {e}") from e

    def delete(self, resource_id: Any) -> None:
        """Delete items from storage that match the keys"""
        try:
            self._query_table().delete().eq(self._id_column, resource_id).execute()
            return None

        except Exception as e:
            raise RuntimeError(f"Failed to delete data: {e}") from e
