"""Code for mocking out agents for testing."""

from typing import Any, Callable, Iterable, List, Optional

from openai.types import CompletionUsage
from openai.types.chat.chat_completion import (
    Choice as CompletionChoice,
    ChatCompletion as OpenAIChatCompletion,
)

from ..completions import (
    ChatCompletion,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionToolChoiceOptionParam,
)
from .protocol import BaseAgent, CompletionCallback, PreCompletionFn
from ..memory import SupportsMemory
from ..workflow import SupportsWorkflow


class MockAgent(BaseAgent):
    """A mock agent for testing. Does not make inference requests."""

    _completion_fn: Callable[[], ChatCompletion]
    _pre_completion_fns: List[PreCompletionFn]
    _completion_callbacks: List[CompletionCallback]
    _memory: Optional[SupportsMemory] = None

    def __init__(
        self,
        completion_fn: Callable[[], ChatCompletion],
        pre_completion_fns: Optional[List[PreCompletionFn]] = None,
        completion_callbacks: Optional[List[CompletionCallback]] = None,
        memory: Optional[SupportsMemory] = None,
    ):
        self._completion_fn = completion_fn
        self._pre_completion_fns = pre_completion_fns or []
        self._completion_callbacks = completion_callbacks or []
        self._memory = memory

    def create_completion(
        self,
        *,
        messages: List[ChatCompletionMessageParam],
        model: Optional[str] = None,
        tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
        tools: Optional[Iterable[ChatCompletionToolParam]] = None,
        response_model: Optional[Any] = None,
        workflow: Optional[SupportsWorkflow] = None,
        **kwargs: Any,
    ) -> ChatCompletion:
        for fn in self._pre_completion_fns:
            messages = fn(messages)
        cmpl = self._completion_fn()
        if self._memory:
            self._memory.store_memory(
                messages=messages, completion=cmpl, workflow=workflow
            )
        self._trigger_completion_callbacks(messages, cmpl)
        return ChatCompletion.from_original_completion(
            original_completion=cmpl, structured_output=None
        )

    def _trigger_completion_callbacks(
        self, messages: List[ChatCompletionMessageParam], completion: ChatCompletion
    ) -> None:
        for fn in self._completion_callbacks:
            fn(messages, completion)

    def count_tokens(self, s: str) -> int:
        return 42


_COMPLETION_ID = "chatcmpl-95LUxn8nTls6Ti5ES1D5LRXv4lwTg"
_CREATED = 1711061307


def new_mock_completion(content: Optional[str] = None) -> ChatCompletion:
    """Create new mock completion"""
    return ChatCompletion.from_original_completion(new_mock_orig_completion(content))


def new_mock_orig_completion(content: Optional[str] = None) -> OpenAIChatCompletion:
    """Create a new original mock completion"""
    if content is None:
        # pylint: disable=line-too-long
        content = "No, I am not sentient. I am a computer program designed to assist with tasks and provide information."

    return OpenAIChatCompletion(
        id=_COMPLETION_ID,
        choices=[
            CompletionChoice(
                finish_reason="stop",
                index=0,
                logprobs=None,
                message=ChatCompletionMessage(
                    # pylint: disable=line-too-long
                    content=content,
                    role="assistant",
                    function_call=None,
                    tool_calls=None,
                ),
            )
        ],
        created=_CREATED,
        model="gpt-3.5-turbo-0125",
        object="chat.completion",
        system_fingerprint="fp_fa89f7a861",
        usage=CompletionUsage(completion_tokens=21, prompt_tokens=11, total_tokens=32),
    )


# This lets us make sure that MockAgent implements the BaseAgent
def _check(_c: BaseAgent) -> None:
    pass


_check(MockAgent(completion_fn=new_mock_completion))
