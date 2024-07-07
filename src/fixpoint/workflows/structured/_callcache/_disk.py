"""Call cache that stores to disk"""

__all__ = [
    "StepDiskCallCache",
    "TaskDiskCallCache",
]

import json
import tempfile
from typing import Any, Optional, Type

import diskcache

from fixpoint._constants import (
    DEFAULT_DISK_CACHE_SIZE_LIMIT_BYTES as DEFAULT_SIZE_LIMIT_BYTES,
)
from ._shared import (
    CallCache,
    CallCacheKind,
    CacheResult,
    serialize_step_cache_key,
    serialize_task_cache_key,
    default_json_dumps,
    T,
    logger,
)
from ._converter import value_to_type


class StepDiskCallCache(CallCache):
    """An on-disk call-cache for steps"""

    cache_kind = CallCacheKind.STEP
    _ttl_s: Optional[float]

    def __init__(
        self,
        cache_dir: str,
        ttl_s: Optional[float] = None,
        size_limit_bytes: int = DEFAULT_SIZE_LIMIT_BYTES,
    ) -> None:
        self._cache = diskcache.Cache(directory=cache_dir, size_limit=size_limit_bytes)
        self._ttl_s = ttl_s

    @classmethod
    def from_tmpdir(
        cls,
        ttl_s: Optional[float] = None,
        size_limit_bytes: int = DEFAULT_SIZE_LIMIT_BYTES,
    ) -> "StepDiskCallCache":
        """Create a new cache from inside a temporary directory"""
        cache_dir = tempfile.mkdtemp()
        return cls(cache_dir, ttl_s, size_limit_bytes)

    def check_cache(
        self,
        run_id: str,
        kind_id: str,
        serialized_args: str,
        type_hint: Optional[Type[Any]] = None,
    ) -> CacheResult[T]:
        key = serialize_step_cache_key(
            run_id=run_id, step_id=kind_id, args=serialized_args
        )
        if key in self._cache:
            logger.debug(f"Cache hit for step {kind_id} with key {key}")
            return CacheResult[T](
                found=True, result=_deserialize_val(self._cache[key], type_hint)
            )
        logger.debug(f"Cache miss for step {kind_id} with key {key}")
        return CacheResult[T](found=False, result=None)

    def store_result(
        self, run_id: str, kind_id: str, serialized_args: str, res: Any
    ) -> None:
        key = serialize_step_cache_key(
            run_id=run_id, step_id=kind_id, args=serialized_args
        )
        res_serialized = default_json_dumps(res)
        self._cache.set(key, res_serialized, expire=self._ttl_s)
        logger.debug(f"Stored result for step {kind_id} with key {key}")


class TaskDiskCallCache(CallCache):
    """An on-disk call-cache for tasks"""

    cache_kind = CallCacheKind.TASK

    def __init__(
        self,
        cache_dir: str,
        ttl_s: Optional[float] = None,
        size_limit_bytes: int = DEFAULT_SIZE_LIMIT_BYTES,
    ) -> None:
        self._cache = diskcache.Cache(directory=cache_dir, size_limit=size_limit_bytes)
        self._ttl_s = ttl_s

    @classmethod
    def from_tmpdir(
        cls,
        ttl_s: Optional[float] = None,
        size_limit_bytes: int = DEFAULT_SIZE_LIMIT_BYTES,
    ) -> "TaskDiskCallCache":
        """Create a new cache from inside a temporary directory"""
        cache_dir = tempfile.mkdtemp()
        return cls(cache_dir, ttl_s, size_limit_bytes)

    def check_cache(
        self,
        run_id: str,
        kind_id: str,
        serialized_args: str,
        type_hint: Optional[Type[Any]] = None,
    ) -> CacheResult[T]:
        key = serialize_task_cache_key(
            run_id=run_id, task_id=kind_id, args=serialized_args
        )
        if key in self._cache:
            logger.debug(f"Cache hit for task {kind_id} with key {key}")
            return CacheResult[T](
                found=True, result=_deserialize_val(self._cache[key], type_hint)
            )
        logger.debug(f"Cache miss for task {kind_id} with key {key}")
        return CacheResult[T](found=False, result=None)

    def store_result(
        self, run_id: str, kind_id: str, serialized_args: str, res: Any
    ) -> None:
        key = serialize_task_cache_key(
            run_id=run_id, task_id=kind_id, args=serialized_args
        )
        res_serialized = default_json_dumps(res)
        self._cache.set(key, res_serialized, expire=self._ttl_s)
        logger.debug(f"Stored result for task {kind_id} with key {key}")


def _deserialize_val(
    value_str: str,
    type_hint: Optional[Type[Any]] = None,
) -> Any:
    deserialized = json.loads(value_str)
    if type_hint is None:
        return deserialized
    return value_to_type(hint=type_hint, value=deserialized)
