from fixpoint.completions import ChatCompletion, ChatCompletionChunk
from fixpoint.agents.mock import MockAgent, new_mock_completion
from fixpoint.memory import WithMemory
from fixpoint.utils import messages


class TestMockAgent:
    def test_completion_memory(self) -> None:
        mem = WithMemory()
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
        assert mems[0][0] == [
            messages.smsg("I am a system"),
            messages.umsg("I am a user"),
        ]
        assert mems[0][1] == cmpl
        assert mems[0][1].choices[0].message.content == "test 0"


class MockCompletionGenerator:
    _num: int

    def __init__(self) -> None:
        self._num = 0

    def new_mock_completion(self) -> ChatCompletion:
        cmpl = new_mock_completion(content=f"test {self._num}")
        self._num += 1
        return cmpl
