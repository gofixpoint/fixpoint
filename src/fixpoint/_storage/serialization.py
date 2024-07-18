"""Storage serialization and deserialization"""

__all__ = ["V", "get_deserialized_data"]

from typing import Any, cast, Dict, get_origin, Type, TypeVar, Union

from pydantic import BaseModel

from .protocol import SupportsSerialization


V = TypeVar("V", bound=Union[BaseModel, SupportsSerialization[Any]])


def get_deserialized_data(value_type: Type[V], data: Dict[str, Any]) -> V:
    """Deserialize a data dictionary into an instance of value_type"""

    # If a class inherits from a generic class, it is not directly an
    # instance of `type`, but is instead an instance of
    # `typing.GenericAlias`. You can access the type under the alias by
    # using `typing.get_origin`.
    origin_type = get_origin(value_type)
    if origin_type is None:
        origin_type = value_type
    if isinstance(origin_type, type) and issubclass(origin_type, SupportsSerialization):
        return cast(V, origin_type.deserialize(data=data))
    elif isinstance(origin_type, type) and issubclass(origin_type, BaseModel):
        return cast(V, value_type(**data))
    else:
        raise TypeError(f"The type {value_type} does not support deserialization")
