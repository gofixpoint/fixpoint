from dataclasses import dataclass
import pytest
from typing import Tuple

from pydantic import BaseModel

from fixpoint.agents.mock import new_mock_completion
from fixpoint.completions.chat_completion import ChatCompletion
from fixpoint.cache import (
    SupportsChatCompletionCache,
    CreateChatCompletionRequest,
    ChatCompletionDiskTLRUCache,
    ChatCompletionTLRUCache,
    ChatCompletionTLRUCacheItem,
)
from fixpoint_extras.workflows.imperative.config import (
    create_chat_completion_cache_supabase_storage,
)
from ..supabase_test_utils import supabase_setup_url_and_key, is_supabase_enabled


class MyModel(BaseModel):
    name: str
    age: int


class TestChatCompletionCache:
    @pytest.mark.skipif(
        not is_supabase_enabled(),
        reason="Disabled until we have a supabase instance running in CI",
    )
    @pytest.mark.parametrize(
        "supabase_setup_url_and_key",
        [
            (
                f"""
        CREATE TABLE IF NOT EXISTS public.completion_cache (
            key text PRIMARY KEY,
            value jsonb NOT NULL,
            ttl float NOT NULL,
            expires_at float NOT NULL
        );

        TRUNCATE TABLE public.completion_cache
        """,
                "public.completion_cache",
            )
        ],
        indirect=True,
    )
    def test_storage_tlru_cache(
        self, supabase_setup_url_and_key: Tuple[str, str]
    ) -> None:
        url, key = supabase_setup_url_and_key
        storage = create_chat_completion_cache_supabase_storage(url, key)
        cache = ChatCompletionTLRUCache(maxsize=50, ttl_s=60 * 60, storage=storage)
        self.assert_cache_hits(cache)

    def test_tlru_cache(self) -> None:
        cache = ChatCompletionTLRUCache(maxsize=50, ttl_s=60 * 60)
        self.assert_cache_hits(cache)

    def test_disk_tlru_cache(self) -> None:
        cache = ChatCompletionDiskTLRUCache.from_tmpdir(
            size_limit_bytes=1024 * 1024, ttl_s=10
        )
        self.assert_cache_hits(cache)

    def assert_cache_hits(self, cache: SupportsChatCompletionCache) -> None:
        req: CreateChatCompletionRequest[MyModel] = {
            "messages": [{"role": "user", "content": "something goes here"}],
            "model": "gpt-3.5-turbo",
            "response_model": MyModel,
            "temperature": None,
            "tool_choice": None,
            "tools": None,
        }

        cache.set(
            req,
            new_mock_completion(
                "this is a faked response", MyModel(name="John", age=20)
            ),
        )

        # make sure that if we create a new list but it has the same contents,
        # we get the same response
        assert cache.get(
            CreateChatCompletionRequest(**req), MyModel
        ) == new_mock_completion(
            "this is a faked response", MyModel(name="John", age=20)
        )

        @dataclass
        class TestCase:
            old_req: CreateChatCompletionRequest[MyModel]
            new_req: CreateChatCompletionRequest[MyModel]
            old_resp: ChatCompletion[MyModel]
            new_resp: ChatCompletion[MyModel]

        req2 = req.copy()
        req2["temperature"] = 0.5
        req3 = req.copy()
        req3["model"] = "gpt-4"
        test_cases = [
            TestCase(
                old_req=req,
                new_req=req2,
                old_resp=new_mock_completion(
                    "this is a faked response", MyModel(name="John", age=20)
                ),
                new_resp=new_mock_completion(
                    "another faked response", MyModel(name="Bob", age=86)
                ),
            ),
            TestCase(
                old_req=req,
                new_req=req3,
                old_resp=new_mock_completion(
                    "this is a faked response", MyModel(name="John", age=20)
                ),
                new_resp=new_mock_completion(
                    "new model response", MyModel(name="Susy", age=42)
                ),
            ),
        ]

        for tc in test_cases:
            assert cache.get(tc.new_req) is None
            cache.set(tc.new_req, tc.new_resp)
            assert cache.get(tc.old_req, MyModel) == tc.old_resp
            assert cache.get(tc.new_req, MyModel) == tc.new_resp

        # # Try changing the temperature, and we should get a different response
        # req2 = req.copy()
        # req2["temperature"] = 0.5
        # assert cache.get(CreateChatCompletionRequest(**req2), MyModel) is None
        # cache.set(req2, new_mock_completion("another faked response", MyModel(name="Bob", age=90)))
        # assert (
        #     cache.get(CreateChatCompletionRequest(**req2), MyModel)
        #     == new_mock_completion("another faked response", MyModel(name="Bob", age=90))
        # )
        # assert (
        #     cache.get(CreateChatCompletionRequest(**req), MyModel)
        #     == new_mock_completion("this is a faked response", MyModel(name="John", age=20))
        # )

        # # Try changing the model, and we should get a different response
        # req3 = req.copy()
        # req3["model"] = "gpt-4"
        # assert cache.get(CreateChatCompletionRequest(**req3), MyModel) is None
        # cache.set(req3, new_mock_completion("another faked response", MyModel(name="Susy", age=42)))
        # assert (
        #     cache.get(CreateChatCompletionRequest(**req3), MyModel)
        #     == new_mock_completion("another faked response", MyModel(name="Susy", age=42))
        # )
        # assert (
        #     cache.get(CreateChatCompletionRequest(**req), MyModel)
        #     == new_mock_completion("this is a faked response", MyModel(name="John", age=20))
        # )
