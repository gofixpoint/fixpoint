from typing import List

from fixpoint.completions import ChatCompletionMessageParam
from fixpoint.memory import WithMemory
from fixpoint.agents.mock import new_mock_completion


class TestWithMemory:
    def test_store_memory(self) -> None:
        memstore = WithMemory()
        assert memstore.memory() == []
        msgs: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": "hello!"}
        ]
        cmpl = new_mock_completion()
        memstore.store_memory(msgs, cmpl)
        assert memstore.memory() == [(msgs, cmpl)]
