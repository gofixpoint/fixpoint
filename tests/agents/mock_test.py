from typing import List
from freezegun import freeze_time

from fixpoint.completions import ChatCompletion, ChatCompletionMessageParam
from fixpoint.agents.mock import MockAgent, new_mock_completion
from fixpoint.memory import Memory
from fixpoint.utils import messages
from fixpoint.cache.tlru import TLRUCache


class TestMockAgent:
    def test_completion_memory(self) -> None:
        mem = Memory()
        agent = MockAgent(
            completion_fn=MockCompletionGenerator().new_mock_completion, memory=mem
        )

        assert mem.memory() == []
        cmpl = agent.create_completion(
            messages=[
                messages.smsg("I am a system"),
                messages.umsg("I am a user"),
            ]
        )
        assert cmpl.choices[0].message.content == "test 0"
        mems = mem.memory()
        assert len(mems) == 1
        assert mems[0].messages == [
            messages.smsg("I am a system"),
            messages.umsg("I am a user"),
        ]
        assert mems[0].completion.choices[0].message.content == "test 0"

    @freeze_time("2023-01-01 00:00:00")
    def test_tlru_cache_ttl(self) -> None:

        cache = TLRUCache[List[ChatCompletionMessageParam], ChatCompletion](
            maxsize=10, ttl=10
        )

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

        # Advance time by 12 seconds so the cache item can expire
        with freeze_time("2023-01-01 00:00:12"):
            assert cache.get(msgs) is None  # evicted
            assert cache.currentsize == 0

            cmpl = agent.create_completion(messages=msgs)
            assert cache.currentsize == 1
            assert mock_gen.num_calls() == 2


class MockCompletionGenerator:
    _num: int

    def __init__(self) -> None:
        self._num = 0

    def new_mock_completion(self) -> ChatCompletion:
        cmpl = new_mock_completion(content=f"test {self._num}")
        self._num += 1
        return cmpl

    def num_calls(self) -> int:
        return self._num
