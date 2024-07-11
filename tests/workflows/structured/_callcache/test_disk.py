from dataclasses import dataclass
from typing import Type
import pytest

from pydantic import BaseModel

from fixpoint.workflows.structured._callcache import CacheResult
from fixpoint.workflows.structured._callcache._disk import (
    StepDiskCallCache,
    TaskDiskCallCache,
)

from .assertions import assert_cache_works


@dataclass
class RetDataClass:
    val: int


class RetPydantic(BaseModel):
    val: int


class TestDiskCallCache:
    @pytest.mark.parametrize("cache_cls", [StepDiskCallCache, TaskDiskCallCache])
    def test_basic(
        self, cache_cls: Type[StepDiskCallCache | TaskDiskCallCache]
    ) -> None:
        cache = cache_cls.from_tmpdir()
        assert_cache_works(cache)

    @pytest.mark.parametrize("cache_cls", [StepDiskCallCache, TaskDiskCallCache])
    def test_pydantic(
        self, cache_cls: Type[StepDiskCallCache | TaskDiskCallCache]
    ) -> None:
        cache = cache_cls.from_tmpdir()

        res = RetPydantic(val=0)
        cache.store_result(run_id="run", kind_id="kind", serialized_args="s0", res=res)
        cached: CacheResult[RetPydantic] = cache.check_cache(
            run_id="run", kind_id="kind", serialized_args="s0", type_hint=RetPydantic
        )
        assert cached.found
        assert cached.result == res

    @pytest.mark.parametrize("cache_cls", [StepDiskCallCache, TaskDiskCallCache])
    def test_dataclass(
        self, cache_cls: Type[StepDiskCallCache | TaskDiskCallCache]
    ) -> None:
        cache = cache_cls.from_tmpdir()

        res = RetDataClass(val=0)
        cache.store_result(run_id="run", kind_id="kind", serialized_args="s0", res=res)
        cached: CacheResult[RetDataClass] = cache.check_cache(
            run_id="run", kind_id="kind", serialized_args="s0", type_hint=RetDataClass
        )
        assert cached.found
        assert cached.result == res
