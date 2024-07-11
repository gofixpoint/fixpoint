from typing import Type
import pytest

from fixpoint.workflows.structured._callcache._in_mem import (
    StepInMemCallCache,
    TaskInMemCallCache,
)

from .assertions import assert_cache_works


class TestInMemCallCache:
    @pytest.mark.parametrize("cache_cls", [StepInMemCallCache, TaskInMemCallCache])
    def test_basic(
        self, cache_cls: Type[StepInMemCallCache | TaskInMemCallCache]
    ) -> None:
        cache = cache_cls()
        assert_cache_works(cache)
