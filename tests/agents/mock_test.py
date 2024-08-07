import json
from typing import List
from freezegun import freeze_time

from pydantic import BaseModel

from fixpoint.completions import ChatCompletion, ChatCompletionMessageParam
from fixpoint.agents.mock import MockAgent, new_mock_completion
from fixpoint.memory import Memory
from fixpoint.utils import messages
from fixpoint.cache import CreateChatCompletionRequest
from fixpoint.cache.tlru import ChatCompletionTLRUCache


class TestMockAgent:
    def test_completion_memory(self) -> None:
        mem = Memory()
        agent = MockAgent(
            completion_fn=MockCompletionGenerator().new_mock_completion, memory=mem
        )

        assert list(mem.memories()) == []
        cmpl = agent.create_completion(
            messages=[
                messages.smsg("I am a system"),
                messages.umsg("I am a user"),
            ]
        )
        assert cmpl.choices[0].message.content == "test 0"
        mems = list(mem.memories())
        assert len(mems) == 1
        assert mems[0].messages == [
            messages.smsg("I am a system"),
            messages.umsg("I am a user"),
        ]
        assert mems[0].completion.choices[0].message.content == "test 0"

    @freeze_time("2023-01-01 00:00:00")
    def test_tlru_cache_ttl(self) -> None:

        cache = ChatCompletionTLRUCache(maxsize=10, ttl_s=10)

        mock_gen = MockCompletionGenerator()
        agent = MockAgent(completion_fn=mock_gen.new_mock_completion, cache=cache)

        # Mock gen not called yet
        assert mock_gen.num_calls() == 0

        msgs: List[ChatCompletionMessageParam] = [
            messages.smsg("I am a system"),
            messages.umsg("I am a user"),
        ]
        cmpl = agent.create_completion(messages=msgs)
        assert cmpl.choices[0].message.content == "test 0"
        assert cache.currentsize == 1
        assert cache.maxsize == 10
        assert mock_gen.num_calls() == 1

        # Making the same call will also yield current size == 1 due to the cache hit
        cmpl = agent.create_completion(messages=msgs)
        assert cache.currentsize == 1
        assert mock_gen.num_calls() == 1

        req = CreateChatCompletionRequest[BaseModel](
            messages=msgs,
            response_model=None,
            temperature=None,
            model="gpt-3.5-turbo-0125",
            tool_choice=None,
            tools=None,
        )

        # Advance time by 12 seconds so the cache item can expire
        with freeze_time("2023-01-01 00:00:12"):
            assert cache.get(req, response_model=None) is None  # evicted
            assert cache.currentsize == 0

            cmpl = agent.create_completion(messages=msgs)
            assert cache.currentsize == 1
            assert mock_gen.num_calls() == 2


class MockCompletionGenerator:
    _num: int

    def __init__(self) -> None:
        self._num = 0

    def new_mock_completion(self) -> ChatCompletion[BaseModel]:
        cmpl: ChatCompletion[BaseModel] = new_mock_completion(
            content=f"test {self._num}"
        )
        self._num += 1
        return cmpl

    def num_calls(self) -> int:
        return self._num
