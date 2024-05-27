from typing import List

from fixpoint.completions import ChatCompletionMessageParam
from fixpoint.memory import Memory, MemoryItem
from fixpoint.agents.mock import new_mock_completion


class TestWithMemory:
    def test_store_memory(self) -> None:
        memstore = Memory()
        assert memstore.memory() == []
        msgs: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": "hello!"}
        ]
        cmpl = new_mock_completion()
        memstore.store_memory(msgs, cmpl)
        assert memstore.memory() == [MemoryItem(messages=msgs, completion=cmpl)]
