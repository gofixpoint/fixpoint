from dataclasses import dataclass
from typing import Dict, List, Type

from pydantic import BaseModel
import pytest

from fixpoint_extras.workflows.structured._callcache import (
    serialize_args,
    CacheResult,
    StepInMemCallCache,
    TaskInMemCallCache,
)


class PBMInner(BaseModel):
    key200: Dict[str, int]
    key100: int


class PBM(BaseModel):
    xyz: PBMInner
    abc: Dict[str, int]
    middle: List[str]


@dataclass
class DCInner:
    key200: Dict[str, int]
    key100: int


@dataclass
class DC:
    xyz: DCInner
    abc: Dict[str, int]
    middle: List[str]


class TestSerializeArgs:
    def test_serialize_basic(self) -> None:
        assert serialize_args(1, 2, 3) == '{"args":[1,2,3],"kwargs":{}}'
        assert (
            serialize_args(1, 2, 3, a=4, b=5, c=6)
            == '{"args":[1,2,3],"kwargs":{"a":4,"b":5,"c":6}}'
        )
        assert (
            serialize_args(1, 2, 3, a=4, b=5, c=6, d=[7, 8, 9])
            == '{"args":[1,2,3],"kwargs":{"a":4,"b":5,"c":6,"d":[7,8,9]}}'
        )

        assert (
            serialize_args(1, [2, 3], 30, a=4, b=5, c=6, d=[7, 8, 9])
            == '{"args":[1,[2,3],30],"kwargs":{"a":4,"b":5,"c":6,"d":[7,8,9]}}'
        )

    def test_serialize_pydantic(self) -> None:
        pbm = PBM(
            xyz=PBMInner(key200={"x": 99, "a": 50}, key100=100),
            abc={"x": 2000, "a": 3000},
            middle=["a", "b", "c"],
        )
        assert (
            serialize_args(pbm, "something_else", foo="bar")
            == '{"args":[{"abc":{"a":3000,"x":2000},"middle":["a","b","c"],"xyz":{"key100":100,"key200":{"a":50,"x":99}}},"something_else"],"kwargs":{"foo":"bar"}}'
        )

    def test_serialize_dataclass(self) -> None:
        pbm = DC(
            xyz=DCInner(key200={"x": 99, "a": 50}, key100=100),
            abc={"x": 2000, "a": 3000},
            middle=["a", "b", "c"],
        )
        assert (
            serialize_args(pbm, "something_else", foo="bar")
            == '{"args":[{"abc":{"a":3000,"x":2000},"middle":["a","b","c"],"xyz":{"key100":100,"key200":{"a":50,"x":99}}},"something_else"],"kwargs":{"foo":"bar"}}'
        )

    def test_serialize_keyorder(self) -> None:
        assert (
            serialize_args(1, {"b": 200, "a": 100}, x=50, a=4, d={"xyz": 90, "abc": 10})
            == '{"args":[1,{"a":100,"b":200}],"kwargs":{"a":4,"d":{"abc":10,"xyz":90},"x":50}}'
        )


class TestInMemCallCache:
    @pytest.mark.parametrize("cache_cls", [StepInMemCallCache, TaskInMemCallCache])
    def test_basic(
        self, cache_cls: Type[StepInMemCallCache | TaskInMemCallCache]
    ) -> None:
        cache = cache_cls()
        pbm = DC(
            xyz=DCInner(key200={"x": 99, "a": 50}, key100=100),
            abc={"x": 2000, "a": 3000},
            middle=["a", "b", "c"],
        )
        serialized = serialize_args(pbm, "something_else", foo="bar")

        res: CacheResult[str] = cache.check_cache(
            run_id="run-1", kind_id="my-kind", serialized_args=serialized
        )
        assert not res.found

        cache.store_result(
            run_id="run-1", kind_id="my-kind", serialized_args=serialized, res="result0"
        )

        # recreate the args and see if we get the right result
        pbm_new = DC(
            xyz=DCInner(key200={"x": 99, "a": 50}, key100=100),
            abc={"x": 2000, "a": 3000},
            middle=["a", "b", "c"],
        )
        serialized_new = serialize_args(pbm_new, "something_else", foo="bar")
        res_new: CacheResult[str] = cache.check_cache(
            run_id="run-1", kind_id="my-kind", serialized_args=serialized_new
        )
        assert res_new.found
        assert res_new.result == "result0"

        # With a different workflow run, we get a different result
        res_diff_run: CacheResult[str] = cache.check_cache(
            run_id="run-2", kind_id="my-kind", serialized_args=serialized_new
        )
        assert not res_diff_run.found

        # with a different step/task ID, we get a different result
        res_diff_kind: CacheResult[str] = cache.check_cache(
            run_id="run-1", kind_id="my-kind-2", serialized_args=serialized_new
        )
        assert not res_diff_kind.found
