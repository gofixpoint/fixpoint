"""
This module contains the OpenAIAgent class, which is responsible for handling the
interaction between the user and OpenAI.
"""

from dataclasses import dataclass
from typing import (
    Any,
    Iterable,
    List,
    Mapping,
    Optional,
    Type,
    TypeVar,
    Union,
    get_args,
    cast,
)

import openai
from pydantic import BaseModel

# Importing these is kind of a hack because they are in a private namespace from
# OpenAI. But we need them because the OpenAI client does not type-check when
# you pass in "None" values for arguments to create chat completions.
from openai._types import NOT_GIVEN as OPENAI_NOT_GIVEN
import instructor
import tiktoken

from fixpoint.cache import SupportsChatCompletionCache, CreateChatCompletionRequest
from fixpoint._protocols.workflow_run import WorkflowRunData
from ..completions import (
    ChatCompletion,
    ChatCompletionMessageParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
)
from ..memory import SupportsMemory, NoOpMemory
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
    def from_api_key(
        cls,
        api_key: str,
        base_url: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
    ) -> "OpenAIClients":
        """Creates our OpenAI clients from an API key"""
        # Create two versions so that we can use the instructor client for
        # structured output and the openai client for everything else.
        # We duplicate the inner OpenAI client in case Instructor mutates it.
        obj = cls(
            openai=openai.OpenAI(
                api_key=api_key, base_url=base_url, default_headers=default_headers
            ),
            instructor=instructor.from_openai(
                openai.OpenAI(
                    api_key=api_key, base_url=base_url, default_headers=default_headers
                )
            ),
        )
        return obj

    def set_base_url(self, base_url: Union[str, None]) -> None:
        """Set the API base URL for the openai client"""
        # the OpenAI class has a property setter that expects either an
        # `httpx.URL` or a `str`, but mypy gets confused.
        self.openai.base_url = base_url  # type: ignore
        instructor_client = self.instructor.client
        if instructor_client is not None:
            instructor_client.base_url = base_url

    # We dont' support setting the customer headers after creating the objects,
    # because the OpenAI default headers are immutable.
    #
    # def set_default_headers(
    #     self, default_headers: Union[Mapping[str, str], None]
    # ) -> None:
    #     """Set the API base URL for the openai client"""
    #     self.openai.default_headers = default_headers
    #     instructor_client = self.instructor.client
    #     if instructor_client is not None:
    #         instructor_client.default_headers = default_headers


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
        # if instance of models is not one of the supported models, raise ValueError
        supported_models = list(get_args(openai.types.ChatModel))
        if model_name not in supported_models + ["<NOT_SET>"]:
            raise ValueError(
                f"Invalid model name: {model_name}. Supported models are: {supported_models}"
            )
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

        basemodel_fixp_completion = cast(ChatCompletion[BaseModel], fixp_completion)
        if self.memory is not None:
            self.memory.store_memory(
                self.id, messages, basemodel_fixp_completion, workflow_run
            )
        self._trigger_completion_callbacks(messages, basemodel_fixp_completion)
        return fixp_completion

    def _request_completion(
        self,
        req: CreateChatCompletionRequest[T_contra],
        **kwargs: Any,
    ) -> ChatCompletion[T_contra]:
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

        if ((req["tool_choice"] is not None) or (req["tools"] is not None)) and (
            req["response_model"] is not None
        ):
            raise ValueError(
                "Explicit tool calls are not supported with structured output."
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

    # TODO(dbmikus) this does not work when we call
    # `self.chat.completions.create` because that is a blind pass-through call
    # to the OpenAI client class, so we have no way to control it.
    def _trigger_completion_callbacks(
        self,
        messages: List[ChatCompletionMessageParam],
        completion: ChatCompletion[BaseModel],
    ) -> None:
        """Trigger the completion callbacks"""
        for callback in self._completion_callbacks:
            callback(messages, completion)
