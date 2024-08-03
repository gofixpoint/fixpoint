"""Make normal agents interface well with workflows"""

import asyncio
from typing import Any, Iterable, List, Optional, Type, overload

from pydantic import BaseModel

from fixpoint.completions import (
    ChatCompletionMessageParam,
    ChatCompletion,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
)
from fixpoint.agents import CacheMode
from fixpoint.memory import SupportsMemory
from fixpoint.agents.protocol import BaseAgent, AsyncBaseAgent, T_contra
from fixpoint._protocols.workflow_run import WorkflowRunData


class AsyncWorkflowAgent(AsyncBaseAgent):
    """Wraps a normal agent and keeps it up to date with workflow state"""

    _inner_agent: AsyncBaseAgent
    _workflow_run: WorkflowRunData

    def __init__(
        self, inner_agent: AsyncBaseAgent, workflow_run: WorkflowRunData
    ) -> None:
        self._inner_agent = inner_agent
        self._workflow_run = workflow_run

    @property
    def memory(self) -> SupportsMemory:
        """Get the memory container for the agent"""
        return self._inner_agent.memory

    @memory.setter
    def memory(self, _memory: SupportsMemory) -> None:
        """Set the memory container for the agent"""
        raise ValueError("memory cannot be set. It is inferred from the workflow")

    @property
    def id(self) -> str:
        """Get the agent id"""
        return self._inner_agent.id

    @id.setter
    def id(self, _agent_id: str) -> None:
        """Set the agent id"""
        raise ValueError("agent_id cannot be set once already inside a workflow")

    @overload
    async def create_completion(
        self,
        *,
        messages: List[ChatCompletionMessageParam],
        response_model: None = None,
        model: Optional[str] = None,
        workflow_run: Optional[WorkflowRunData] = None,
        tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
        tools: Optional[Iterable[ChatCompletionToolParam]] = None,
        temperature: Optional[float] = None,
        cache_mode: Optional[CacheMode] = "normal",
        **kwargs: Any,
    ) -> ChatCompletion[BaseModel]: ...

    @overload
    async def create_completion(
        self,
        *,
        messages: List[ChatCompletionMessageParam],
        response_model: Type[T_contra],
        model: Optional[str] = None,
        workflow_run: Optional[WorkflowRunData] = None,
        tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
        tools: Optional[Iterable[ChatCompletionToolParam]] = None,
        temperature: Optional[float] = None,
        cache_mode: Optional[CacheMode] = "normal",
        **kwargs: Any,
    ) -> ChatCompletion[T_contra]: ...

    async def create_completion(
        self,
        *,
        messages: List[ChatCompletionMessageParam],
        response_model: Optional[Type[T_contra]] = None,
        model: Optional[str] = None,
        workflow_run: Optional[WorkflowRunData] = None,
        tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
        tools: Optional[Iterable[ChatCompletionToolParam]] = None,
        temperature: Optional[float] = None,
        cache_mode: Optional[CacheMode] = "normal",
        **kwargs: Any,
    ) -> ChatCompletion[T_contra]:
        """Create a completion

        The `model` argument is optional if the agent has a pre-defined model it
        should use. In that case, specifying `model` overrides which model to
        use.
        """
        if workflow_run:
            raise ValueError(
                "workflow_run cannot be passed in. It is inferred from the workflow"
            )
        # we need to have this if/else check so that type-checking works
        async with asyncio.TaskGroup() as tg:
            if response_model:
                task = tg.create_task(
                    self._inner_agent.create_completion(
                        messages=messages,
                        response_model=response_model,
                        model=model,
                        tool_choice=tool_choice,
                        tools=tools,
                        temperature=temperature,
                        cache_mode=cache_mode,
                        workflow_run=self._workflow_run,
                        **kwargs,
                    )
                )
            else:
                task = tg.create_task(
                    self._inner_agent.create_completion(
                        messages=messages,
                        model=model,
                        tool_choice=tool_choice,
                        tools=tools,
                        temperature=temperature,
                        cache_mode=cache_mode,
                        workflow_run=self._workflow_run,
                        **kwargs,
                    )
                )
        return task.result()

    def count_tokens(self, s: str) -> int:
        """Count the tokens in the string, according to the model's agent(s)"""
        return self._inner_agent.count_tokens(s)

    def set_cache_mode(self, mode: CacheMode) -> None:
        """If the agent has a cache, set its cache mode"""
        return self._inner_agent.set_cache_mode(mode)

    def get_cache_mode(self) -> CacheMode:
        """If the agent has a cache, set its cache mode"""
        return self._inner_agent.get_cache_mode()


class WorkflowAgent(BaseAgent):
    """Wraps a normal agent and keeps it up to date with workflow state"""

    _inner_agent: BaseAgent
    _workflow_run: WorkflowRunData

    def __init__(self, inner_agent: BaseAgent, workflow_run: WorkflowRunData) -> None:
        self._inner_agent = inner_agent
        self._workflow_run = workflow_run

    @property
    def memory(self) -> SupportsMemory:
        """Get the memory container for the agent"""
        return self._inner_agent.memory

    @memory.setter
    def memory(self, _memory: SupportsMemory) -> None:
        """Set the memory container for the agent"""
        raise ValueError("memory cannot be set. It is inferred from the workflow")

    @property
    def id(self) -> str:
        """Get the agent id"""
        return self._inner_agent.id

    @id.setter
    def id(self, _agent_id: str) -> None:
        """Set the agent id"""
        raise ValueError("agent_id cannot be set once already inside a workflow")

    @overload
    def create_completion(
        self,
        *,
        messages: List[ChatCompletionMessageParam],
        response_model: None = None,
        model: Optional[str] = None,
        workflow_run: Optional[WorkflowRunData] = None,
        tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
        tools: Optional[Iterable[ChatCompletionToolParam]] = None,
        temperature: Optional[float] = None,
        cache_mode: Optional[CacheMode] = "normal",
        **kwargs: Any,
    ) -> ChatCompletion[BaseModel]: ...

    @overload
    def create_completion(
        self,
        *,
        messages: List[ChatCompletionMessageParam],
        response_model: Type[T_contra],
        model: Optional[str] = None,
        workflow_run: Optional[WorkflowRunData] = None,
        tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
        tools: Optional[Iterable[ChatCompletionToolParam]] = None,
        temperature: Optional[float] = None,
        cache_mode: Optional[CacheMode] = "normal",
        **kwargs: Any,
    ) -> ChatCompletion[T_contra]: ...

    def create_completion(
        self,
        *,
        messages: List[ChatCompletionMessageParam],
        response_model: Optional[Type[T_contra]] = None,
        model: Optional[str] = None,
        workflow_run: Optional[WorkflowRunData] = None,
        tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
        tools: Optional[Iterable[ChatCompletionToolParam]] = None,
        temperature: Optional[float] = None,
        cache_mode: Optional[CacheMode] = "normal",
        **kwargs: Any,
    ) -> ChatCompletion[T_contra]:
        """Create a completion

        The `model` argument is optional if the agent has a pre-defined model it
        should use. In that case, specifying `model` overrides which model to
        use.
        """
        if workflow_run:
            raise ValueError(
                "workflow_run cannot be passed in. It is inferred from the workflow"
            )
        # we need to have this if/else check so that type-checking works
        if response_model:
            return self._inner_agent.create_completion(
                messages=messages,
                response_model=response_model,
                model=model,
                tool_choice=tool_choice,
                tools=tools,
                temperature=temperature,
                cache_mode=cache_mode,
                workflow_run=self._workflow_run,
                **kwargs,
            )
        else:
            return self._inner_agent.create_completion(
                messages=messages,
                model=model,
                tool_choice=tool_choice,
                tools=tools,
                temperature=temperature,
                cache_mode=cache_mode,
                workflow_run=self._workflow_run,
                **kwargs,
            )

    def count_tokens(self, s: str) -> int:
        """Count the tokens in the string, according to the model's agent(s)"""
        return self._inner_agent.count_tokens(s)

    def set_cache_mode(self, mode: CacheMode) -> None:
        """If the agent has a cache, set its cache mode"""
        return self._inner_agent.set_cache_mode(mode)

    def get_cache_mode(self) -> CacheMode:
        """If the agent has a cache, set its cache mode"""
        return self._inner_agent.get_cache_mode()
