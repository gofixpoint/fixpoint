"""Supabase storage"""

from typing import Any, Optional
from supabase import create_client, Client
from .protocol import SupportsStorage


class SupabaseStorage(SupportsStorage):
    """Supabase storage"""

    def __init__(self, url: str, key: str, default_table: Optional[str] = None):
        self._default_table = default_table
        try:
            self._client: Client = create_client(url, key)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Supabase: {e}") from e

    def _query_table(self, resource: Optional[str] = None) -> Any:
        lookup_table = resource or self._default_table
        if lookup_table is None:
            raise ValueError(
                "Either table must be provided or default_table must be set"
            )
        return self._client.table(lookup_table)

    def fetch_latest(
        self,
        n: Optional[int] = None,
        resource: Optional[str] = None,
        order_key: Optional[str] = "id",
        model: Optional[Any] = None,
    ) -> Any:
        """Fetch the latest n items from the storage"""
        try:
            query = self._query_table(resource).select("*").order(order_key, desc=True)
            if n:
                result = query.limit(n).execute()
            else:
                result = query.execute()
            if model:
                return [model(**item) for item in result.data]
            return result.data
        except Exception as e:
            raise RuntimeError(f"Failed to fetch latest data: {e}") from e

    def fetch(
        self,
        filter_criteria: dict[str, Any],
        resource: Optional[str] = None,
        model: Optional[Any] = None,
    ) -> Any:
        """Fetch data items from storage"""
        try:
            query = self._query_table(resource).select("*")
            for k, v in filter_criteria.items():
                query = query.eq(k, v)
            result = query.execute()
            if model:
                return [model(**item) for item in result.data]
            return result.data
        except Exception as e:
            raise RuntimeError(f"Failed to fetch data: {e}") from e

    def insert(
        self, data: Any, resource: Optional[str] = None, model: Optional[Any] = None
    ) -> Any:
        """Insert data items to storage"""
        try:
            query = self._query_table(resource)
            result = query.insert(data).execute()
            if model:
                return [model(**item) for item in result.data]
            return result.data
        except Exception as e:
            raise RuntimeError(f"Failed to insert data: {e}") from e

    def update(
        self,
        data: Any,
        resource: Optional[str] = None,
        model: Optional[Any] = None,
    ) -> Any:
        """Update items in storage (uses upsert)"""
        try:
            query = self._query_table(resource)
            result = query.upsert(data).execute()
            if model:
                return [model(**item) for item in result.data]
            return result.data
        except Exception as e:
            raise RuntimeError(f"Failed to update data: {e}") from e

    def delete(
        self, filter_criteria: dict[str, Any], resource: Optional[str] = None
    ) -> Any:
        """Delete items from storage that match the keys"""
        try:
            query = self._query_table(resource).delete()
            for k, v in filter_criteria.items():
                query = query.eq(k, v)
            resp = query.execute()
            return resp.data
        except Exception as e:
            raise RuntimeError(f"Failed to delete data: {e}") from e
