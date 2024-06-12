"""Pre- and post-inference callback functions."""

from typing import List

import tiktoken

from fixpoint.logging import logger
from fixpoint.completions import (
    ChatCompletionMessageParam,
)


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
