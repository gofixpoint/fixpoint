from fixpoint.completions import ChatCompletion
from fixpoint.cache.disktlru import ChatCompletionDiskTLRUCache
from fixpoint.cache.protocol import CreateChatCompletionRequest
from fixpoint.agents.mock import new_mock_completion

from pydantic import BaseModel


class MyModel(BaseModel):
    name: str
    age: int


class TestDiskTLRUCache:
    def test_messages_serialize(self) -> None:
        cache = ChatCompletionDiskTLRUCache.from_tmpdir(
            size_limit_bytes=1024 * 1024, ttl_s=10
        )

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
