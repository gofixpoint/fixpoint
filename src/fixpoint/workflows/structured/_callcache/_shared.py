"""Module for caching task and step executions."""

__all__ = [
    "CacheResult",
    "CallCache",
    "CallCacheKind",
    "JSONEncoder",
    "logger",
    "serialize_args",
    "serialize_step_cache_key",
    "serialize_task_cache_key",
    "T",
]

import dataclasses
from dataclasses import is_dataclass
from enum import Enum
import json
from typing import Any, Generic, Optional, Protocol, Type, TypeVar

from pydantic import BaseModel

from fixpoint.logging import logger as root_logger


T = TypeVar("T")


class CallCacheKind(Enum):
    """Kind of call cache to use"""

    TASK = "task"
    STEP = "step"


@dataclasses.dataclass
class CacheResult(Generic[T]):
    """The result of a cache check

    The result of a cache check. If there is a cache hit, `found is True`, and
    `result` is of type `T`. If there is a cache miss, `found is False`, and
    `result` is `None`.

    Note that `T` can also be `None` even if there is a cache hit, so don't rely
    on checking `cache_result.result is None`. Check `cache_result.found`.
    """

    found: bool
    result: Optional[T]


class CallCache(Protocol):
    """Protocol for a call cache for tasks or steps"""

    cache_kind: CallCacheKind

    def check_cache(
        self,
        run_id: str,
        kind_id: str,
        serialized_args: str,
        type_hint: Optional[Type[Any]] = None,
    ) -> CacheResult[Any]:
        """Check if the result of a task or step call is cached"""

    def store_result(
        self, run_id: str, kind_id: str, serialized_args: str, res: Any
    ) -> None:
        """Store the result of a task or step call"""


class JSONEncoder(json.JSONEncoder):
    """Encoder to serialize objects to JSON"""

    def default(self, o: Any) -> Any:
        if isinstance(o, BaseModel):
            return o.model_dump()
        if is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def serialize_args(*args: Any, **kwargs: Any) -> str:
    """Serialize arbitrary arguments and keyword arguments to a string"""
    return default_json_dumps({"args": args, "kwargs": kwargs})


def serialize_step_cache_key(*, run_id: str, step_id: str, args: str) -> str:
    """Serialize a step cache key to a string"""
    return default_json_dumps({"run_id": run_id, "step_id": step_id, "args": args})


def serialize_task_cache_key(*, run_id: str, task_id: str, args: str) -> str:
    """Serialize a task cache key to a string"""
    return default_json_dumps({"run_id": run_id, "task_id": task_id, "args": args})


def default_json_dumps(obj: Any) -> str:
    """Default serialization of an object to JSON"""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), cls=JSONEncoder)


logger = root_logger.getChild("workflows.structured._callcache")
