"""shared internal code for the caching module"""

import json
from typing import (
    cast,
    Any,
    Generic,
    Iterable,
    List,
    Optional,
    Type,
    TypedDict,
    TypeVar,
)

from pydantic import BaseModel

from fixpoint.completions import (
    ChatCompletionMessageParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
)
from fixpoint.logging import logger as root_logger


logger = root_logger.getChild("cache")


BM = TypeVar("BM", bound=BaseModel)


class CreateChatCompletionRequest(TypedDict, Generic[BM]):
    """The arguments in a request to create a chat completion"""

    messages: List[ChatCompletionMessageParam]
    model: str
    tool_choice: Optional[ChatCompletionToolChoiceOptionParam]
    tools: Optional[Iterable[ChatCompletionToolParam]]
    response_model: Optional[Type[BM]]
    temperature: Optional[float]


class _CreateChatCompletionRequestModel(BaseModel):
    messages: List[ChatCompletionMessageParam]
    model: str
    tool_choice: Optional[ChatCompletionToolChoiceOptionParam]
    tools: Optional[Iterable[ChatCompletionToolParam]]
    response_model: Optional[BaseModel]
    temperature: Optional[float]


def parse_create_chat_completion_request(
    data: Any,
) -> CreateChatCompletionRequest[BaseModel]:
    """Parse a chat completion request"""
    if not isinstance(data, dict):
        raise ValueError("expected a dictionary")
    return cast(
        CreateChatCompletionRequest[BaseModel],
        _CreateChatCompletionRequestModel(**data).model_dump(),
    )


def serialize_any(key: Any) -> str:
    """Serialize anything to a string"""
    if isinstance(key, (dict, list, set, str, int, float, bool)):
        return json.dumps(key)
    return str(key)


def serialize_chat_completion_request(req: CreateChatCompletionRequest[BM]) -> str:
    """Serialize a chat completion request"""
    reqclone = dict(req)
    resp_model = req["response_model"]
    if resp_model is None:
        reqclone["response_model"] = None
    else:
        reqclone["response_model"] = resp_model.model_json_schema()
    return json.dumps(reqclone)


def deserialize_chat_completion_request(
    sreq: str, response_model: Optional[Type[BM]] = None
) -> CreateChatCompletionRequest[BM]:
    """Deserialize a chat completion request"""
    parsed = json.loads(sreq)
    if parsed["response_model"] is None and response_model is None:
        parsed["response_model"] = None
    elif parsed["response_model"] and response_model:
        parsed["response_model"] = response_model
    else:
        raise TypeError("provided response_model and serialized response_model differ")

    # Make sure the parsed object is valid
    return cast(
        CreateChatCompletionRequest[BM],
        _CreateChatCompletionRequestModel(**parsed).model_dump(),
    )
