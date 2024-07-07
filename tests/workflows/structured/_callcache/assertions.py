from fixpoint.workflows.structured._callcache import (
    CallCache,
    serialize_args,
    CacheResult,
)
from .fixtures import DC, DCInner


def assert_cache_works(cache: CallCache) -> None:
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
