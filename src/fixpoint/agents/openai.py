"""
This module contains the OpenAIAgent class, which is responsible for handling the
interaction between the user and OpenAI.
"""

from dataclasses import dataclass
from typing import Any, Iterable, List, Optional, get_args

import openai

# Importing these is kind of a hack because they are in a private namespace from
# OpenAI. But we need them because the OpenAI client does not type-check when
# you pass in "None" values for arguments to create chat completions.
from openai._types import NOT_GIVEN as OPENAI_NOT_GIVEN
import instructor
import tiktoken

from ..completions import (
    ChatCompletion,
    ChatCompletionMessageParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
)
from ..memory import SupportsMemory
from ..workflow import SupportsWorkflow
from ..cache import ChatCompletionCache
from .protocol import BaseAgent, CompletionCallback, PreCompletionFn
from ._shared import request_cached_completion, CacheMode


@dataclass
class OpenAIClients:
    """
    A class that contains the OpenAI and Instructor clients.
    """

    openai: openai.OpenAI
    instructor: instructor.Instructor

    @classmethod
    def from_api_key(cls, api_key: str) -> "OpenAIClients":
        """Creates our OpenAI clients from an API key"""
        # Create two versions so that we can use the instructor client for
        # structured output and the openai client for everything else.
        # We duplicate the inner OpenAI client in case Instructor mutates it.
        return cls(
            openai=openai.OpenAI(api_key=api_key),
            instructor=instructor.from_openai(openai.OpenAI(api_key=api_key)),
        )


class OpenAIAgent(BaseAgent):
    """
    An agent that follows our BaseAgent protocol, but interacts with OpenAI.
    """

    _openai_clients: OpenAIClients
    _completion_callbacks: List[CompletionCallback]
    _pre_completion_fns: List[PreCompletionFn]
    _memory: Optional[SupportsMemory]
    _cache_mode: CacheMode = "normal"

    def __init__(
        self,
        model_name: str,
        openai_clients: OpenAIClients,
        *,
        pre_completion_fns: Optional[List[PreCompletionFn]] = None,
        completion_callbacks: Optional[List[CompletionCallback]] = None,
        memory: Optional[SupportsMemory] = None,
        cache: Optional[ChatCompletionCache] = None,
    ) -> None:
        # if instance of models is not one of the supported models, raise ValueError
        supported_models = get_args(openai.types.ChatModel)
        if model_name not in supported_models:
            raise ValueError(
                f"Invalid model name: {model_name}. Supported models are: {supported_models}"
            )
        self.model_name = model_name
        self._openai_clients = openai_clients

        self._completion_callbacks = completion_callbacks or []
        self._pre_completion_fns = pre_completion_fns or []
        self._memory = memory
        self._cache = cache

    def create_completion(
        self,
        *,
        messages: List[ChatCompletionMessageParam],
        model: Optional[str] = None,
        workflow: Optional[SupportsWorkflow] = None,
        response_model: Optional[Any] = None,
        tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
        tools: Optional[Iterable[ChatCompletionToolParam]] = None,
        cache_mode: Optional[CacheMode] = None,
        **kwargs: Any,
    ) -> ChatCompletion:
        """Create a completion"""
        if "stream" in kwargs and kwargs["stream"]:
            raise ValueError("Streaming is not supported yet.")

        messages = self._trigger_pre_completion_fns(messages)

        # User can override the model, but by default we use the model they
        # constructed the agent with.
        mymodel = model or self.model_name

        def _wrapped_completion_fn() -> ChatCompletion:
            return self._request_completion(
                messages,
                mymodel,
                response_model,
                tool_choice=tool_choice,
                tools=tools,
                **kwargs,
            )

        if cache_mode is None:
            cache_mode = self._cache_mode
        fixp_completion = request_cached_completion(
            cache=self._cache,
            messages=messages,
            completion_fn=_wrapped_completion_fn,
            cache_mode=cache_mode,
        )

        if self._memory is not None:
            self._memory.store_memory(messages, fixp_completion, workflow)
        self._trigger_completion_callbacks(messages, fixp_completion)
        return fixp_completion

    def _request_completion(
        self,
        messages: List[ChatCompletionMessageParam],
        model: str,
        response_model: Optional[Any] = None,
        tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
        tools: Optional[Iterable[ChatCompletionToolParam]] = None,
        **kwargs: Any,
    ) -> ChatCompletion:
        if response_model is None:
            compl = self._openai_clients.openai.chat.completions.create(
                messages=messages,
                model=model,
                # TODO(dbmikus) support streaming mode.
                stream=False,
                tool_choice=tool_choice or OPENAI_NOT_GIVEN,
                tools=tools or OPENAI_NOT_GIVEN,
                **kwargs,
            )
            return ChatCompletion.from_original_completion(
                original_completion=compl,
                structured_output=None,
            )

        if ((tool_choice is not None) or (tools is not None)) and (
            response_model is not None
        ):
            raise ValueError(
                "Explicit tool calls are not supported with structured output."
            )

        structured_resp, completion = (
            self._openai_clients.instructor.chat.completions.create_with_completion(
                messages=messages,
                model=model,
                # TODO(dbmikus) support streaming mode.
                stream=False,
                response_model=response_model,
                **kwargs,
            )
        )
        return ChatCompletion.from_original_completion(
            original_completion=completion,
            structured_output=structured_resp,
        )

    def count_tokens(self, s: str) -> int:
        """Count the tokens in the string, according to the model's agent(s)"""
        encoding = tiktoken.encoding_for_model(self.model_name)
        return len(encoding.encode(s))

    def set_cache_mode(self, mode: CacheMode) -> None:
        """If the agent has a cache, set its cache mode"""
        self._cache_mode = mode

    def get_cache_mode(self) -> CacheMode:
        """If the agent has a cache, set its cache mode"""
        return self._cache_mode

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


class OpenAI:
    """
    An agent that conforms to the OpenAI API.
    """

    fixp: OpenAIAgent
    _fixpchat: "OpenAI._Chat"

    def __init__(
        self,
        model_name: str,
        openai_clients: OpenAIClients,
        *,
        pre_completion_fns: Optional[List[PreCompletionFn]] = None,
        completion_callbacks: Optional[List[CompletionCallback]] = None,
        memory: Optional[SupportsMemory] = None,
        cache: Optional[ChatCompletionCache] = None,
    ) -> None:
        self.fixp = OpenAIAgent(
            model_name=model_name,
            openai_clients=openai_clients,
            pre_completion_fns=pre_completion_fns,
            completion_callbacks=completion_callbacks,
            memory=memory,
            cache=cache,
        )

        self._fixpchat = OpenAI._Chat(openai_clients.instructor.chat, self.fixp)

    @property
    def chat(self) -> "OpenAI._Chat":
        """Chat-related operations"""
        return self._fixpchat

    def __getattr__(self, name: str) -> Any:
        # Forward attribute access to the underlying client
        return getattr(self._fixpchat, name)

    class _Chat:
        _fixpchat: instructor.Instructor
        _fixpcompletions: "OpenAI._Completions"
        _agent: OpenAIAgent

        def __init__(
            self, openai_chat: instructor.Instructor, agent: OpenAIAgent
        ) -> None:
            self._fixpchat = openai_chat
            self._fixpcompletions = OpenAI._Completions(
                self._fixpchat.completions, agent
            )
            self._agent = agent

        @property
        def completions(self) -> "OpenAI._Completions":
            """Operations on chat completions"""
            return self._fixpcompletions

        def __getattr__(self, name: str) -> Any:
            # Forward attribute access to the underlying client
            return getattr(self._fixpchat, name)

    class _Completions:
        _fixpcompletions: instructor.Instructor
        _agent: OpenAIAgent

        def __init__(
            self, openai_completions: instructor.Instructor, agent: OpenAIAgent
        ) -> None:
            self._fixpcompletions = openai_completions
            self._agent = agent

        def __getattr__(self, name: str) -> Any:
            # Forward attribute access to the underlying client
            return getattr(self._fixpcompletions, name)

        def create(
            self,
            messages: List[ChatCompletionMessageParam],
            *,
            model: Optional[str] = None,
            tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
            tools: Optional[Iterable[ChatCompletionToolParam]] = None,
            response_model: Optional[Any] = None,
            workflow: Optional[SupportsWorkflow] = None,
            **kwargs: Any,
        ) -> ChatCompletion:
            """Create a chat completion"""
            return self._agent.create_completion(
                messages=messages,
                model=model,
                tool_choice=tool_choice,
                tools=tools,
                response_model=response_model,
                workflow=workflow,
                **kwargs,
            )
