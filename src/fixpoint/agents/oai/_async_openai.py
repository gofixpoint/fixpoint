"""A wrapper around the AsyncOpenAI client.

A wrapper around the AsyncOpenAI client that gives it some extra features like
caching, memory, pre-and-post inference callbacks, etc...
"""

__all__ = ["AsyncOpenAI"]

import asyncio
from typing import (
    Any,
    Iterable,
    List,
    Optional,
    Type,
    TypeVar,
    overload,
)

from pydantic import BaseModel
import instructor

from fixpoint.completions import (
    ChatCompletion,
    ChatCompletionMessageParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
)
from fixpoint.memory import SupportsMemory
from fixpoint._protocols.workflow_run import WorkflowRunData
from fixpoint.cache import SupportsChatCompletionCache
from ..openai import AsyncOpenAIAgent, AsyncOpenAIClients
from ..protocol import CompletionCallback, PreCompletionFn


T_contra = TypeVar("T_contra", bound=BaseModel, contravariant=True)


class AsyncOpenAI:
    """
    An agent that conforms to the OpenAI API.
    """

    fixp: AsyncOpenAIAgent
    _fixpchat: "AsyncOpenAI._Chat"
    _model_name: Optional[str]

    def __init__(
        self,
        agent_id: str,
        openai_clients: AsyncOpenAIClients,
        *,
        pre_completion_fns: Optional[List[PreCompletionFn]] = None,
        completion_callbacks: Optional[List[CompletionCallback]] = None,
        memory: Optional[SupportsMemory] = None,
        cache: Optional[SupportsChatCompletionCache] = None,
    ) -> None:
        self.fixp = AsyncOpenAIAgent(
            agent_id=agent_id,
            model_name="<NOT_SET>",
            openai_clients=openai_clients,
            pre_completion_fns=pre_completion_fns,
            completion_callbacks=completion_callbacks,
            memory=memory,
            cache=cache,
        )

        self._fixpchat = AsyncOpenAI._Chat(openai_clients.instructor.chat, self.fixp)

    @property
    def chat(self) -> "AsyncOpenAI._Chat":
        """Chat-related operations"""
        return self._fixpchat

    def __getattr__(self, name: str) -> Any:
        # Forward attribute access to the underlying client
        return getattr(self._fixpchat, name)

    class _Chat:
        _fixpchat: instructor.Instructor
        _fixpcompletions: "AsyncOpenAI._Completions"
        _agent: AsyncOpenAIAgent

        def __init__(
            self, openai_chat: instructor.Instructor, agent: AsyncOpenAIAgent
        ) -> None:
            self._fixpchat = openai_chat
            self._fixpcompletions = AsyncOpenAI._Completions(
                self._fixpchat.completions, agent
            )
            self._agent = agent

        @property
        def completions(self) -> "AsyncOpenAI._Completions":
            """Operations on chat completions"""
            return self._fixpcompletions

        def __getattr__(self, name: str) -> Any:
            # Forward attribute access to the underlying client
            return getattr(self._fixpchat, name)

    class _Completions:
        _fixpcompletions: instructor.Instructor
        _agent: AsyncOpenAIAgent

        def __init__(
            self, openai_completions: instructor.Instructor, agent: AsyncOpenAIAgent
        ) -> None:
            self._fixpcompletions = openai_completions
            self._agent = agent

        def __getattr__(self, name: str) -> Any:
            # Forward attribute access to the underlying client
            return getattr(self._fixpcompletions, name)

        @overload
        async def create(
            self,
            messages: List[ChatCompletionMessageParam],
            *,
            model: str,
            response_model: None = None,
            tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
            tools: Optional[Iterable[ChatCompletionToolParam]] = None,
            temperature: Optional[float] = None,
            workflow_run: Optional[WorkflowRunData] = None,
            **kwargs: Any,
        ) -> ChatCompletion[BaseModel]: ...

        @overload
        async def create(
            self,
            messages: List[ChatCompletionMessageParam],
            *,
            model: str,
            response_model: Type[T_contra],
            tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
            tools: Optional[Iterable[ChatCompletionToolParam]] = None,
            temperature: Optional[float] = None,
            workflow_run: Optional[WorkflowRunData] = None,
            **kwargs: Any,
        ) -> ChatCompletion[T_contra]: ...

        async def create(
            self,
            messages: List[ChatCompletionMessageParam],
            *,
            model: str,
            response_model: Optional[Type[T_contra]] = None,
            temperature: Optional[float] = None,
            tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
            tools: Optional[Iterable[ChatCompletionToolParam]] = None,
            workflow_run: Optional[WorkflowRunData] = None,
            **kwargs: Any,
        ) -> ChatCompletion[T_contra]:
            """Create a chat completion"""
            async with asyncio.TaskGroup() as tg:
                cmpl_t = tg.create_task(
                    self._agent.create_completion(
                        messages=messages,
                        model=model,
                        temperature=temperature,
                        tool_choice=tool_choice,
                        tools=tools,
                        response_model=response_model,
                        workflow_run=workflow_run,
                        **kwargs,
                    )
                )
            return cmpl_t.result()
