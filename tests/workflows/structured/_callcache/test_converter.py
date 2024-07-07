import json
from typing import get_type_hints

from fixpoint.workflows.structured._callcache._shared import default_json_dumps
from fixpoint.workflows.structured._callcache._converter import value_to_type

from .fixtures import PBM, PBMInner, DC, DCInner


def test_pydantic_converter() -> None:

    def make_pbm(inner: PBMInner) -> PBM:
        return PBM(xyz=inner, abc={"a": 1, "b": 2}, middle=["a", "b", "c"])

    inner = PBMInner(key200={"a": 1, "b": 2}, key100=3)
    computed_res = make_pbm(inner)

    serialized_res = default_json_dumps(computed_res)

    type_hint = get_type_hints(make_pbm)["return"]

    deserialized_res = value_to_type(type_hint, json.loads(serialized_res))

    assert isinstance(deserialized_res, PBM)
    assert deserialized_res == computed_res


def test_dataclass_converter() -> None:

    def make_dc(inner: DCInner) -> DC:
        return DC(xyz=inner, abc={"a": 1, "b": 2}, middle=["a", "b", "c"])

    inner = DCInner(key200={"a": 1, "b": 2}, key100=3)
    computed_res = make_dc(inner)

    serialized_res = default_json_dumps(computed_res)

    type_hint = get_type_hints(make_dc)["return"]

    deserialized_res = value_to_type(type_hint, json.loads(serialized_res))

    assert isinstance(deserialized_res, DC)
    assert deserialized_res == computed_res
