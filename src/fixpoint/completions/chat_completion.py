"""
LLM ChatCompletions
"""

from typing import Any, Optional, List, Literal

from pydantic import Field, PrivateAttr
from openai.types.completion_usage import CompletionUsage
from openai.types.chat import ChatCompletionChunk
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion import (
    ChatCompletion as OpenAIChatCompletion,
    Choice,
)
from openai.types.chat.chat_completion_message import ChatCompletionMessage


# Define this externally because below we have a method that overrides the
# `object` name.
def _raw_set_attr(obj: Any, name: str, value: Any) -> None:
    """
    Set an attribute on an object without triggering any of the pydantic logic.
    """
    object.__setattr__(obj, name, value)


class ChatCompletion(OpenAIChatCompletion):
    """
    A class that wraps a completion with a Fixpoint completion.
    """

    _original_completion: OpenAIChatCompletion = PrivateAttr()
    fixp: "ChatCompletion.Fixp" = Field(exclude=True)

    class Fixp:
        """
        A class that represents a Fixpoint completion.
        """

        _structured_output: Optional[Any]

        def __init__(self, structured_output: Optional[Any] = None) -> None:
            self.structured_output = structured_output

    # pylint: disable=super-init-not-called
    def __init__(
        self,
        *,
        # these are from the parent class
        id: str,  # pylint: disable=redefined-builtin
        choices: List[Choice],
        created: int,
        model: str,
        object: Literal["chat.completion"],  # pylint: disable=redefined-builtin
        system_fingerprint: Optional[str] = None,
        usage: Optional[CompletionUsage] = None,
        # we added these
        structured_output: Optional[Any] = None
    ) -> None:
        # Normally, we should call the superclass here, but since we are doing a
        # weird implementation where we pass calls through to the parent via the
        # `__getattr__` method, we don't need to do that.
        orig_completion = OpenAIChatCompletion(
            id=id,
            choices=choices,
            created=created,
            model=model,
            object=object,
            system_fingerprint=system_fingerprint,
            usage=usage,
        )
        _raw_set_attr(self, "_original_completion", orig_completion)
        _raw_set_attr(self, "fixp", ChatCompletion.Fixp(structured_output))

    @classmethod
    def from_original_completion(
        cls,
        original_completion: OpenAIChatCompletion,
        structured_output: Optional[Any] = None,
    ) -> "ChatCompletion":
        """
        Create a new ChatCompletion from an original completion.
        """
        return cls(
            id=original_completion.id,
            choices=original_completion.choices,
            created=original_completion.created,
            model=original_completion.model,
            object=original_completion.object,
            system_fingerprint=original_completion.system_fingerprint,
            usage=original_completion.usage,
            structured_output=structured_output,
        )

    def __getattr__(self, name: str) -> Any:
        # Forward attribute access to the underlying client
        return getattr(self._original_completion, name)


__all__ = [
    "ChatCompletion",
    "ChatCompletionMessage",
    "ChatCompletionMessageParam",
    "ChatCompletionChunk",
]
