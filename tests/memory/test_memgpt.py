from typing import List

from fixpoint.memory import Memory
from fixpoint.completions import ChatCompletion, ChatCompletionMessageParam
from fixpoint.agents.mock import MockAgent, new_mock_completion
from fixpoint.utils.messages import smsg, umsg
from fixpoint.memory._memgpt import (
    MemGPTSummaryAgent,
    MemGPTSummarizeOpts,
    _ContextLengthCheck,
)


class TestMemGPTSummaryAgent:
    def test_simple_create_completion(self) -> None:
        mem = Memory()
        agent = MockAgent(completion_fn=_completion_fn, memory=mem)
        summary_opts = MemGPTSummarizeOpts(agent=agent, context_window=200)
        summary_agent = MemGPTSummaryAgent(summary_opts)

        compl = summary_agent.create_completion(
            messages=[
                smsg(
                    "You are a friendly AI customer support agent. You chat with a user to answer their questions"
                ),
                umsg("What is your name?"),
            ]
        )

        # We are under the token limit, so we don't summarize.
        assert len(mem.memory()) == 1
        # We are under the token limit, so we did not summarize and product any
        # extra messages.
        assert len(mem.memory()[0][0]) == 2


def test_context_length_check() -> None:
    agent = MockAgent(
        completion_fn=_completion_fn,
    )
    summary_opts = MemGPTSummarizeOpts(agent=agent, context_window=200)
    messages: List[ChatCompletionMessageParam] = []
    extra_messages: List[ChatCompletionMessageParam] = [
        smsg(
            "You are a friendly AI customer support agent. You chat with a user to answer their questions"
        ),
        umsg("What is your name?"),
    ]
    lencheck = _ContextLengthCheck.from_opts_and_messages(
        opts=summary_opts,
        messages=messages,
        extra_preserved_messages=extra_messages,
    )

    # Make sure that the context length check does not modify either of the
    # lists.
    assert len(messages) == 0
    assert len(extra_messages) == 2


def _completion_fn() -> ChatCompletion:
    return new_mock_completion(
        "I am a friendly AI customer support agent here to assist you with any questions or issues you may have. How can I help you today?"
    )
