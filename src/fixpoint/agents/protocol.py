"""A base protocol for agents"""

from typing import Any, Callable, List, Protocol

import tiktoken

from ..logging import logger
from ..chat import ChatCompletionMessageParam, ChatCompletion


class BaseAgent(Protocol):
    """The base protocol for agents"""

    def create_completion(
        self, *, messages: List[ChatCompletionMessageParam], **kwargs: Any
    ) -> ChatCompletion:
        """Create a completion"""

    def count_tokens(self, s: str) -> int:
        """Count the tokens in the string, according to the model's agent(s)"""


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
