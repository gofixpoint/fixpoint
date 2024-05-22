from freezegun import freeze_time
from fixpoint.cache.tlru import TLRUCache


class TestTLRUCache:

    def test_tlru_cache_size_limits(self) -> None:
        ttlCache = TLRUCache[str, str](maxsize=1)
        ttlCache.set("test", "a", 1000)
        ttlCache.set("test2", "b", 1000)
        ttlCache.set("test3", "c", 1000)

        assert ttlCache.currentsize == 1
        assert ttlCache.maxsize == 1
        assert ttlCache.get("test") is None  # evicted
        assert ttlCache.get("test2") is None  # evicted
        assert ttlCache.get("test3") == "c"

    @freeze_time("2023-01-01")
    def test_tlru_cache_ttl(self) -> None:
        ttlCache = TLRUCache[str, str](maxsize=1)
        ttlCache.set("test", "a", 10)
        assert ttlCache.get("test") == "a"

        # Advance time by 12 seconds
        with freeze_time("2023-01-01 00:00:12"):
            assert ttlCache.get("test") is None  # evicted
