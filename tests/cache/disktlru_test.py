from typing import List

from fixpoint.cache.disktlru import DiskTLRUCache
from fixpoint.completions import ChatCompletionMessageParam


class TestDiskTLRUCache:
    def test_messages_serialize(self) -> None:
        cache = DiskTLRUCache[List[ChatCompletionMessageParam], str].from_tmpdir(
            size_limit_bytes=1024 * 1024, ttl_s=10
        )

        cache.set(
            [{"role": "user", "content": "something goes here"}],
            "this is a faked response",
        )

        # make sure that if we create a new list but it has the same contents,
        # we get the same response
        assert (
            cache.get([{"role": "user", "content": "something goes here"}])
            == "this is a faked response"
        )
