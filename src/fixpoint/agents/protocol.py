"""A base protocol for agents"""

from typing import Any, Callable, Iterable, List, Optional, Protocol, Type

from pydantic import BaseModel
import tiktoken

from ..logging import logger
from ..completions import (
    ChatCompletionMessageParam,
    ChatCompletion,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
)
from ..workflow import SupportsWorkflow
from ._shared import CacheMode


class BaseAgent(Protocol):
    """The base protocol for agents"""

    def create_completion(
        self,
        *,
        messages: List[ChatCompletionMessageParam],
        model: Optional[str] = None,
        workflow: Optional[SupportsWorkflow] = None,
        response_model: Optional[Type[BaseModel]] = None,
        tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
        tools: Optional[Iterable[ChatCompletionToolParam]] = None,
        cache_mode: Optional[CacheMode] = "normal",
        **kwargs: Any,
    ) -> ChatCompletion:
        """Create a completion

        The `model` argument is optional if the agent has a pre-defined model it
        should use. In that case, specifying `model` overrides which model to
        use.
        """

    def count_tokens(self, s: str) -> int:
        """Count the tokens in the string, according to the model's agent(s)"""

    def set_cache_mode(self, mode: CacheMode) -> None:
        """If the agent has a cache, set its cache mode"""

    def get_cache_mode(self) -> CacheMode:
        """If the agent has a cache, set its cache mode"""


PreCompletionFn = Callable[
    [List[ChatCompletionMessageParam]], List[ChatCompletionMessageParam]
]

CompletionCallback = Callable[[List[ChatCompletionMessageParam], ChatCompletion], None]


class TikTokenLogger:
    """A completion callback class for logging the number of tokens in the messages"""

    _tokenizer: tiktoken.Encoding

    def __init__(self, model_name: str):
        self._tokenizer = tiktoken.encoding_for_model(model_name)

    def tiktoken_logger(
        self, messages: List[ChatCompletionMessageParam]
    ) -> List[ChatCompletionMessageParam]:
        """Log the number of tokens in the messages"""

        # TODO(dbmikus) I'm not sure if this is how OpenAI combines multiple
        # message objects into a single string before tokenizing.
        joined = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        tokenized = self._tokenizer.encode(joined)

        # TODO(dbmikus) replace with a logger
        # logger.info(f"Total input tokens: {len(tokenized)}")
        logger.info("Total input tokens: %s", len(tokenized))
        return messages
