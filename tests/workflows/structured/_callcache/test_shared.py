from fixpoint.workflows.structured._callcache._shared import (
    serialize_args,
)

from .fixtures import PBM, PBMInner, DC, DCInner


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
