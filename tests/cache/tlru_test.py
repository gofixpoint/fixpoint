from typing import Tuple, Any
import json
import pytest
from freezegun import freeze_time
from fixpoint.cache.tlru import TLRUCache, TLRUCacheItem
from fixpoint.storage.supabase import SupabaseStorage
from ..supabase_test_utils import supabase_setup_url_and_key, is_supabase_enabled


class TestTLRUCache:

    def test_tlru_cache_size_limits(self) -> None:
        ttlCache = TLRUCache[str, str](
            maxsize=1, ttl_s=1000, serialize_key_fn=json.dumps
        )
        ttlCache.set("test", "a")
        ttlCache.set("test2", "b")
        ttlCache.set("test3", "c")

        assert ttlCache.currentsize == 1
        assert ttlCache.maxsize == 1
        assert ttlCache.get("test") is None  # evicted
        assert ttlCache.get("test2") is None  # evicted
        assert ttlCache.get("test3") == "c"

    @freeze_time("2023-01-01 00:00:00")
    def test_tlru_cache_ttl(self) -> None:
        ttlCache = TLRUCache[str, str](maxsize=1, ttl_s=10, serialize_key_fn=json.dumps)
        ttlCache.set("test", "a")
        assert ttlCache.get("test") == "a"

        # Advance time by 12 seconds
        with freeze_time("2023-01-01 00:00:12"):
            assert ttlCache.get("test") is None  # evicted


@pytest.mark.skipif(
    not is_supabase_enabled(),
    reason="Disabled until we have a supabase instance running in CI",
)
@freeze_time("2023-01-01 00:00:00")
class TestTLRUCacheWithStorage:

    @freeze_time("2023-01-01 00:00:00")
    @pytest.mark.parametrize(
        "supabase_setup_url_and_key",
        [
            (
                f"""
        CREATE TABLE IF NOT EXISTS public.completion_cache (
            key text PRIMARY KEY,
            value jsonb,
            ttl float,
            expires_at float
        );

        TRUNCATE TABLE public.completion_cache
        """,
                "public.completion_cache",
            )
        ],
        indirect=True,
    )
    def test_tlru_cache_with_storage(
        self, supabase_setup_url_and_key: Tuple[str, str]
    ) -> None:
        url, key = supabase_setup_url_and_key

        class MockChatCompletion:
            request: list[dict[str, str]]
            response: str

            def __init__(self, request: list[dict[str, str]], response: str) -> None:
                self.request = request
                self.response = response

            def to_dict(self) -> dict[str, Any]:
                return {"request": self.request, "response": self.response}

        completion = MockChatCompletion(
            [{"role": "user", "content": "something goes here"}],
            "this is a faked response",
        )

        storage = SupabaseStorage(
            url,
            key,
            table="completion_cache",
            order_key="expires_at",
            id_column="key",
            # We cannot not specify the generic type parameter for
            # TLRUCacheItem, because then when we try to do `isinstance(cls,
            # type)`, the class will actually be a `typing.GenericAlias` and not
            # a type (class definition).
            value_type=TLRUCacheItem,
        )

        cache = TLRUCache[list[dict[str, str]], str](
            maxsize=10, ttl_s=10, serialize_key_fn=json.dumps, storage=storage
        )

        item_key = completion.request
        item_serialized_key = json.dumps(item_key)
        item_value = completion.response
        # Assert that the completion is not stored in cache nor storage
        assert cache.get(item_key) is None

        # map the request to the entire completion object
        cache.set(item_key, item_value)

        assert cache.get(item_key) == item_value
        stored_item = storage.fetch(item_serialized_key)
        assert stored_item is not None
        assert stored_item.key == item_key
        assert stored_item.value == item_value
        assert stored_item.ttl == 10
        assert stored_item.expires_at is not None

        # Instantiate cache from data, we should get one item in the cache
        new_cache = TLRUCache[list[dict[str, str]], str](
            maxsize=10, ttl_s=10, serialize_key_fn=json.dumps, storage=storage
        )
        assert new_cache.get(item_key) == item_value
        # Instantiate cache from data, after ttl has expired, we should get no items in the cache
        with freeze_time("2023-01-01 00:00:22"):
            another_cache = TLRUCache[list[dict[str, str]], str](
                maxsize=10, ttl_s=10, serialize_key_fn=json.dumps, storage=storage
            )
            # Not initialized with any data from the storage
            assert another_cache.get(item_key) is None

            # Check that the item is also gone from storage
            stored_item = storage.fetch(item_serialized_key)
            assert stored_item is None
