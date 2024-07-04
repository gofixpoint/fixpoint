"""Module for caching task and step executions."""

# TODO(dbmikus) for on-disk or in-DB store, try using dacite or Temporal
# converter.py[1] for deserialization.
#
# The problem is serializing and deserializing dataclasses.
#
# [1]: sdk-python/temporalio/converter.py

import dataclasses
from dataclasses import is_dataclass
from enum import Enum
import json
from typing import Any, Dict, Generic, Optional, Protocol, TypeVar

from pydantic import BaseModel

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
        self, run_id: str, kind_id: str, serialized_args: str
    ) -> CacheResult[Any]:
        """Check if the result of a task or step call is cached"""

    def store_result(
        self, run_id: str, kind_id: str, serialized_args: str, res: Any
    ) -> None:
        """Store the result of a task or step call"""


class StepInMemCallCache(CallCache):
    """An in-memory call-cache for steps"""

    cache_kind = CallCacheKind.STEP
    kind_id: str
    _cache: Dict[str, Any]

    def __init__(self) -> None:
        self._cache = {}

    def check_cache(
        self, run_id: str, kind_id: str, serialized_args: str
    ) -> CacheResult[T]:
        key = _serialize_step_cache_key(
            run_id=run_id, step_id=kind_id, args=serialized_args
        )
        if key not in self._cache:
            return CacheResult[T](found=False, result=None)
        return CacheResult[T](found=True, result=self._cache[key])

    def store_result(
        self, run_id: str, kind_id: str, serialized_args: str, res: Any
    ) -> None:
        key = _serialize_step_cache_key(
            run_id=run_id, step_id=kind_id, args=serialized_args
        )
        self._cache[key] = res


class TaskInMemCallCache(CallCache):
    """An in-memory call-cache for tasks"""

    cache_kind = CallCacheKind.TASK
    kind_id: str
    _cache: Dict[str, Any]

    def __init__(self) -> None:
        self._cache = {}

    def check_cache(
        self, run_id: str, kind_id: str, serialized_args: str
    ) -> CacheResult[T]:
        key = _serialize_task_cache_key(
            run_id=run_id, task_id=kind_id, args=serialized_args
        )
        if key not in self._cache:
            return CacheResult[T](found=False, result=None)
        return CacheResult[T](found=True, result=self._cache[key])

    def store_result(
        self, run_id: str, kind_id: str, serialized_args: str, res: Any
    ) -> None:
        key = _serialize_task_cache_key(
            run_id=run_id, task_id=kind_id, args=serialized_args
        )
        self._cache[key] = res


def serialize_args(*args: Any, **kwargs: Any) -> str:
    """Serialize arbitrary arguments and keyword arguments to a string"""
    return _default_json_dumps({"args": args, "kwargs": kwargs})


class _JSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, BaseModel):
            return o.model_dump()
        if is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def _serialize_step_cache_key(*, run_id: str, step_id: str, args: str) -> str:
    return _default_json_dumps({"run_id": run_id, "step_id": step_id, "args": args})


def _serialize_task_cache_key(*, run_id: str, task_id: str, args: str) -> str:
    return _default_json_dumps({"run_id": run_id, "task_id": task_id, "args": args})


def _default_json_dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), cls=_JSONEncoder)
