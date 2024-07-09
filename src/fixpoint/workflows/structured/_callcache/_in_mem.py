"""In-memory call-cache"""

__all__ = ["StepInMemCallCache", "TaskInMemCallCache"]

from typing import Any, Dict

from ._shared import (
    CallCache,
    CallCacheKind,
    CacheResult,
    serialize_step_cache_key,
    serialize_task_cache_key,
    T,
)


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
        key = serialize_step_cache_key(
            run_id=run_id, step_id=kind_id, args=serialized_args
        )
        if key not in self._cache:
            return CacheResult[T](found=False, result=None)
        return CacheResult[T](found=True, result=self._cache[key])

    def store_result(
        self, run_id: str, kind_id: str, serialized_args: str, res: Any
    ) -> None:
        key = serialize_step_cache_key(
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
        key = serialize_task_cache_key(
            run_id=run_id, task_id=kind_id, args=serialized_args
        )
        if key not in self._cache:
            return CacheResult[T](found=False, result=None)
        return CacheResult[T](found=True, result=self._cache[key])

    def store_result(
        self, run_id: str, kind_id: str, serialized_args: str, res: Any
    ) -> None:
        key = serialize_task_cache_key(
            run_id=run_id, task_id=kind_id, args=serialized_args
        )
        self._cache[key] = res
