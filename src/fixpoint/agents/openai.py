"""
This module contains the OpenAIAgent class, which is responsible for handling the
interaction between the user and OpenAI.
"""

from typing import Any, List, Optional, cast, get_args

import openai
import instructor
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion import ChatCompletion
import tiktoken

from .._utils.completions import decorate_instructor_completion_with_fixp
from .protocol import BaseAgent, CompletionCallback, PreCompletionFn
from ..memory import WithMemoryProto


class OpenAIAgent(BaseAgent):
    """
    This is the Agent class.
    """

    _client: instructor.Instructor
    _completion_callbacks: List[CompletionCallback]
    _pre_completion_fns: List[PreCompletionFn]
    _memory: Optional[WithMemoryProto]

    def __init__(
        self,
        model_name: str,
        api_key: str,
        *,
        pre_completion_fns: Optional[List[PreCompletionFn]] = None,
        completion_callbacks: Optional[List[CompletionCallback]] = None,
        memory: Optional[WithMemoryProto] = None,
    ) -> None:
        # if instance of models is not one of the supported models, raise ValueError
        supported_models = get_args(openai.types.ChatModel)
        if model_name not in supported_models:
            raise ValueError(
                f"Invalid model name: {model_name}. Supported models are: {supported_models}"
            )
        if api_key is None:
            raise ValueError("API key must be provided to use OpenAI models.")
        self.model_name = model_name

        # Wrap the openai client with instructor
        self._client = instructor.from_openai(openai.OpenAI(api_key=api_key))

        # Replace call to chat.completions.create with
        # chat.completions.create_with_completion which will expose
        # the response object and the original response
        decorated_method = decorate_instructor_completion_with_fixp(
            self._client.chat.completions.create_with_completion
        )

        setattr(self._client.chat.completions, "create", decorated_method)

        self._completion_callbacks = completion_callbacks or []
        self._pre_completion_fns = pre_completion_fns or []
        self._memory = memory

    def __getattr__(self, name: str) -> Any:
        # Forward attribute access to the underlying client
        return getattr(self._client, name)

    def create_completion(
        self,
        *,
        messages: List[ChatCompletionMessageParam],
        **kwargs: Any,
    ) -> ChatCompletion:
        """Create a completion"""
        if "stream" in kwargs and kwargs["stream"]:
            raise ValueError("Streaming is not supported yet.")

        messages = self._trigger_pre_completion_fns(messages)

        completion = self._client.chat.completions.create(
            messages=messages,
            model=self.model_name,
            # TODO(dbmikus) support streaming mode.
            stream=False,
            **kwargs,
        )
        # For some reason, the type checker doesn't understand that the type of
        # completion is ChatCompletion.
        # Note, when we support streaming, the return type will be different
        # depending on whether streaming is on or off.
        fixed_completion = cast(ChatCompletion, completion)

        if self._memory is not None:
            self._memory.store_memory(messages, fixed_completion)
        self._trigger_completion_callbacks(messages, fixed_completion)
        return fixed_completion

    def count_tokens(self, s: str) -> int:
        """Count the tokens in the string, according to the model's agent(s)"""
        encoding = tiktoken.encoding_for_model(self.model_name)
        return len(encoding.encode(s))

    def _trigger_pre_completion_fns(
        self, messages: List[ChatCompletionMessageParam]
    ) -> List[ChatCompletionMessageParam]:
        """Trigger the pre-completion functions"""
        for fn in self._pre_completion_fns:
            messages = fn(messages)
        return messages

    # TODO(dbmikus) this does not work when we call
    # `self.chat.completions.create` because that is a blind pass-through call
    # to the OpenAI client class, so we have no way to control it.
    def _trigger_completion_callbacks(
        self, messages: List[ChatCompletionMessageParam], completion: ChatCompletion
    ) -> None:
        """Trigger the completion callbacks"""
        for callback in self._completion_callbacks:
            callback(messages, completion)
