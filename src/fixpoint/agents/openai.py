"""
This module contains the OpenAIAgent class, which is responsible for handling the
interaction between the user and OpenAI.
"""

__all__ = ["OpenAIAgent", "AsyncOpenAIAgent", "OpenAIClients", "AsyncOpenAIClients"]


import asyncio
from typing import Any, Iterable, List, Optional, Type, TypeVar, get_args, cast

import openai
from pydantic import BaseModel

# Importing these is kind of a hack because they are in a private namespace from
# OpenAI. But we need them because the OpenAI client does not type-check when
# you pass in "None" values for arguments to create chat completions.
from openai._types import NOT_GIVEN as OPENAI_NOT_GIVEN
import tiktoken

from fixpoint.cache import SupportsChatCompletionCache, CreateChatCompletionRequest
from fixpoint._protocols.workflow_run import WorkflowRunData
from fixpoint.completions import (
    ChatCompletion,
    ChatCompletionMessageParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
)
from fixpoint.memory import SupportsMemory, NoOpMemory
from .protocol import BaseAgent, AsyncBaseAgent, CompletionCallback, PreCompletionFn
from ._shared import request_cached_completion, arequest_cached_completion, CacheMode
from ._openai_clients import OpenAIClients, AsyncOpenAIClients


T_contra = TypeVar("T_contra", bound=BaseModel, contravariant=True)


class OpenAIAgent(BaseAgent):
    """
    An agent that follows our BaseAgent protocol, but interacts with OpenAI.
    """

    _openai_clients: OpenAIClients
    _completion_callbacks: List[CompletionCallback]
    _pre_completion_fns: List[PreCompletionFn]
    _cache_mode: CacheMode = "normal"

    memory: SupportsMemory
    id: str

    def __init__(
        self,
        agent_id: str,
        model_name: str,
        openai_clients: OpenAIClients,
        *,
        pre_completion_fns: Optional[List[PreCompletionFn]] = None,
        completion_callbacks: Optional[List[CompletionCallback]] = None,
        memory: Optional[SupportsMemory] = None,
        cache: Optional[SupportsChatCompletionCache] = None,
    ) -> None:
        _validate_supported_models(model_name)
        self.model_name = model_name
        self._openai_clients = openai_clients
        self._completion_callbacks = completion_callbacks or []
        self._pre_completion_fns = pre_completion_fns or []
        self.memory = memory or NoOpMemory()
        self._cache = cache
        self.id = agent_id

    def create_completion(
        self,
        *,
        messages: List[ChatCompletionMessageParam],
        model: Optional[str] = None,
        workflow_run: Optional[WorkflowRunData] = None,
        response_model: Optional[Type[T_contra]] = None,
        tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
        tools: Optional[Iterable[ChatCompletionToolParam]] = None,
        temperature: Optional[float] = None,
        cache_mode: Optional[CacheMode] = None,
        **kwargs: Any,
    ) -> ChatCompletion[T_contra]:
        """Create a completion"""
        if "stream" in kwargs and kwargs["stream"]:
            raise ValueError("Streaming is not supported yet.")

        messages = self._trigger_pre_completion_fns(messages)

        # User can override the model, but by default we use the model they
        # constructed the agent with.
        mymodel = model or self.model_name

        req = CreateChatCompletionRequest(
            messages=messages,
            model=mymodel,
            tool_choice=tool_choice,
            tools=tools,
            response_model=response_model,
            temperature=temperature,
        )

        def _wrapped_completion_fn() -> ChatCompletion[T_contra]:
            return self._request_completion(
                req,
                **kwargs,
            )

        if cache_mode is None:
            cache_mode = self._cache_mode
        fixp_completion = request_cached_completion(
            cache=self._cache,
            req=req,
            completion_fn=_wrapped_completion_fn,
            cache_mode=cache_mode,
        )

        _post_process_completion(
            agent_id=self.id,
            workflow_run=workflow_run,
            input_messages=messages,
            cmpl=fixp_completion,
            memory_store=self.memory,
            callbacks=self._completion_callbacks,
        )

        return fixp_completion

    def _request_completion(
        self,
        req: CreateChatCompletionRequest[T_contra],
        **kwargs: Any,
    ) -> ChatCompletion[T_contra]:
        _validate_create_chat_completion_request(req)

        if req["response_model"] is None:
            compl = self._openai_clients.openai.chat.completions.create(
                messages=req["messages"],
                model=req["model"],
                # TODO(dbmikus) support streaming mode.
                stream=False,
                tool_choice=req["tool_choice"] or OPENAI_NOT_GIVEN,
                tools=req["tools"] or OPENAI_NOT_GIVEN,
                **kwargs,
            )
            return ChatCompletion.from_original_completion(
                original_completion=compl,
                structured_output=None,
            )

        structured_resp, completion = (
            self._openai_clients.instructor.chat.completions.create_with_completion(
                messages=req["messages"],
                model=req["model"],
                # TODO(dbmikus) support streaming mode.
                stream=False,
                # Instructor gets weird if this is a BaseModel type, even though it is
                response_model=cast(Any, req["response_model"]),
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


class AsyncOpenAIAgent(AsyncBaseAgent):
    """
    An async agent that follows our AsyncBaseAgent protocol, but interacts with OpenAI.
    """

    _openai_clients: AsyncOpenAIClients
    _completion_callbacks: List[CompletionCallback]
    _pre_completion_fns: List[PreCompletionFn]
    _cache_mode: CacheMode = "normal"

    memory: SupportsMemory
    id: str

    def __init__(
        self,
        agent_id: str,
        model_name: str,
        openai_clients: AsyncOpenAIClients,
        *,
        pre_completion_fns: Optional[List[PreCompletionFn]] = None,
        completion_callbacks: Optional[List[CompletionCallback]] = None,
        memory: Optional[SupportsMemory] = None,
        cache: Optional[SupportsChatCompletionCache] = None,
    ) -> None:
        _validate_supported_models(model_name)
        self.model_name = model_name
        self._openai_clients = openai_clients
        self._completion_callbacks = completion_callbacks or []
        self._pre_completion_fns = pre_completion_fns or []
        self.memory = memory or NoOpMemory()
        self._cache = cache
        self.id = agent_id

    async def create_completion(
        self,
        *,
        messages: List[ChatCompletionMessageParam],
        model: Optional[str] = None,
        workflow_run: Optional[WorkflowRunData] = None,
        response_model: Optional[Type[T_contra]] = None,
        tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
        tools: Optional[Iterable[ChatCompletionToolParam]] = None,
        temperature: Optional[float] = None,
        cache_mode: Optional[CacheMode] = None,
        **kwargs: Any,
    ) -> ChatCompletion[T_contra]:
        """Create a completion"""
        if "stream" in kwargs and kwargs["stream"]:
            raise ValueError("Streaming is not supported yet.")

        messages = self._trigger_pre_completion_fns(messages)

        req = CreateChatCompletionRequest(
            messages=messages,
            # User can override the model, but by default we use the model they
            # constructed the agent with.
            model=model or self.model_name,
            tool_choice=tool_choice,
            tools=tools,
            response_model=response_model,
            temperature=temperature,
        )

        async def _wrapped_completion_fn() -> ChatCompletion[T_contra]:
            return await self._request_completion(
                req,
                **kwargs,
            )

        async with asyncio.TaskGroup() as tg:
            fixp_completion_task = tg.create_task(
                arequest_cached_completion(
                    cache=self._cache,
                    req=req,
                    completion_fn=_wrapped_completion_fn,
                    cache_mode=cache_mode or self._cache_mode,
                )
            )
        fixp_completion = fixp_completion_task.result()

        _post_process_completion(
            agent_id=self.id,
            workflow_run=workflow_run,
            input_messages=messages,
            cmpl=fixp_completion,
            memory_store=self.memory,
            callbacks=self._completion_callbacks,
        )

        return fixp_completion

    async def _request_completion(
        self,
        req: CreateChatCompletionRequest[T_contra],
        **kwargs: Any,
    ) -> ChatCompletion[T_contra]:
        _validate_create_chat_completion_request(req)

        if req["response_model"] is None:
            compl = await self._openai_clients.openai.chat.completions.create(
                messages=req["messages"],
                model=req["model"],
                # TODO(dbmikus) support streaming mode.
                stream=False,
                tool_choice=req["tool_choice"] or OPENAI_NOT_GIVEN,
                tools=req["tools"] or OPENAI_NOT_GIVEN,
                **kwargs,
            )
            return ChatCompletion.from_original_completion(
                original_completion=compl,
                structured_output=None,
            )

        async with asyncio.TaskGroup() as tg:
            cmpl_task = tg.create_task(
                self._openai_clients.instructor.chat.completions.create_with_completion(
                    messages=req["messages"],
                    model=req["model"],
                    # TODO(dbmikus) support streaming mode.
                    stream=False,
                    # Instructor gets weird if this is a BaseModel type, even though it is
                    response_model=cast(Any, req["response_model"]),
                    **kwargs,
                )
            )
        structured_resp, completion = cmpl_task.result()
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


####
# Helper functions for the async and sync agents
####


def _validate_supported_models(model_name: str) -> None:
    supported_models = list(get_args(openai.types.ChatModel))
    if model_name not in supported_models + ["<NOT_SET>"]:
        raise ValueError(
            f"Invalid model name: {model_name}. Supported models are: {supported_models}"
        )


def _validate_create_chat_completion_request(
    req: CreateChatCompletionRequest[T_contra],
) -> None:
    if ((req["tool_choice"] is not None) or (req["tools"] is not None)) and (
        req["response_model"] is not None
    ):
        raise ValueError(
            "Explicit tool calls are not supported with structured output."
        )


def _post_process_completion(
    agent_id: str,
    workflow_run: Optional[WorkflowRunData],
    input_messages: List[ChatCompletionMessageParam],
    cmpl: ChatCompletion[T_contra],
    memory_store: Optional[SupportsMemory],
    callbacks: List[CompletionCallback],
) -> None:
    # Cast to ChatCompletion[BaseModel] because `memory_store.store_memory` and
    # the callbacks expect the `BaseModel` type.
    basemodel_fixp_completion = cast(ChatCompletion[BaseModel], cmpl)
    if memory_store is not None:
        memory_store.store_memory(
            agent_id, input_messages, basemodel_fixp_completion, workflow_run
        )
    for callback in callbacks:
        callback(input_messages, basemodel_fixp_completion)
