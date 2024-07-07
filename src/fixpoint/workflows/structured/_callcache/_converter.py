"""Converting between deserialized and serialized data formats"""

# This file contains code snippets from Temporal.
# licensed under the MIT license.
#
# The MIT License
#
# Copyright (c) 2022 Temporal Technologies Inc.  All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# Modifications:
#
# - dbmikus 2024-07-07: modifications to extract from original converter.py file
#
# Original source:
# https://github.com/temporalio/sdk-python/blob/38d9eefce2795f76fefc7fb5c487d85a5d1f51d9/temporalio/converter.py

__all__ = ["value_to_type"]


from abc import ABC, abstractmethod
import collections
import dataclasses
from enum import IntEnum
import inspect
from typing import (
    Any,
    Dict,
    get_type_hints,
    Literal,
    NewType,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)
import sys
import uuid


if sys.version_info >= (3, 10):
    from types import UnionType

if sys.version_info >= (3, 11):
    from enum import StrEnum


_JSONTypeConverterUnhandled = NewType("_JSONTypeConverterUnhandled", object)


class JSONTypeConverter(ABC):
    """Converter for converting an object from Python :py:func:`json.loads`
    result (e.g. scalar, list, or dict) to a known type.
    """

    Unhandled = _JSONTypeConverterUnhandled(object())
    """Sentinel value that must be used as the result of
    :py:meth:`to_typed_value` to say the given type is not handled by this
    converter."""

    @abstractmethod
    def to_typed_value(
        self, hint: Type[Any], value: Any
    ) -> Union[Optional[Any], _JSONTypeConverterUnhandled]:
        """Convert the given value to a type based on the given hint.

        Args:
            hint: Type hint to use to help in converting the value.
            value: Value as returned by :py:func:`json.loads`. Usually a scalar,
                list, or dict.

        Returns:
            The converted value or :py:attr:`Unhandled` if this converter does
            not handle this situation.
        """
        raise NotImplementedError


# pylint: disable=too-many-branches,too-many-statements,too-many-locals
def value_to_type(
    hint: Type[Any],
    value: Any,
    custom_converters: Optional[Sequence[JSONTypeConverter]] = None,
) -> Any:
    """Convert a given value to the given type hint.

    This is used internally to convert a raw JSON loaded value to a specific
    type hint.

    Args:
        hint: Type hint to convert the value to.
        value: Raw value (e.g. primitive, dict, or list) to convert from.
        custom_converters: Set of custom converters to try before doing default
            conversion. Converters are tried in order and the first value that
            is not :py:attr:`JSONTypeConverter.Unhandled` will be returned from
            this function instead of doing default behavior.

    Returns:
        Converted value.

    Raises:
        TypeError: Unable to convert to the given hint.
    """
    if custom_converters is None:
        custom_converters = []

    # Try custom converters
    for conv in custom_converters:
        ret = conv.to_typed_value(hint, value)
        if ret is not JSONTypeConverter.Unhandled:
            return ret

    # Any or primitives
    if hint is Any:
        return value
    elif hint is int or hint is float:
        if not isinstance(value, (int, float)):
            raise TypeError(f"Expected value to be int|float, was {type(value)}")
        return hint(value)
    elif hint is bool:
        if not isinstance(value, bool):
            raise TypeError(f"Expected value to be bool, was {type(value)}")
        return bool(value)
    elif hint is str:
        if not isinstance(value, str):
            raise TypeError(f"Expected value to be str, was {type(value)}")
        return str(value)
    elif hint is bytes:
        if not isinstance(value, (str, bytes, list)):
            raise TypeError(f"Expected value to be bytes, was {type(value)}")
        # In some other SDKs, this is serialized as a base64 string, but in
        # Python this is a numeric array.
        return bytes(value)  # type: ignore
    elif hint is type(None):
        if value is not None:
            raise TypeError(f"Expected None, got value of type {type(value)}")
        return None

    # NewType. Note we cannot simply check isinstance NewType here because it's
    # only been a class since 3.10. Instead we'll just check for the presence
    # of a supertype.
    supertype = getattr(hint, "__supertype__", None)
    if supertype:
        return value_to_type(supertype, value, custom_converters)

    # Load origin for other checks
    origin = getattr(hint, "__origin__", hint)
    type_args: Tuple[Any, ...] = getattr(hint, "__args__", ())

    # Literal
    if origin is Literal:
        if value not in type_args:
            raise TypeError(f"Value {value} not in literal values {type_args}")
        return value

    is_union = origin is Union
    if sys.version_info >= (3, 10):
        is_union = is_union or isinstance(origin, UnionType)

    # Union
    if is_union:
        # Try each one. Note, Optional is just a union w/ none.
        for arg in type_args:
            try:
                return value_to_type(arg, value, custom_converters)
            except Exception:  # pylint: disable=broad-exception-caught
                pass
        raise TypeError(f"Failed converting to {hint} from {value}")

    # Mapping
    if inspect.isclass(origin) and issubclass(origin, collections.abc.Mapping):
        if not isinstance(value, collections.abc.Mapping):
            raise TypeError(f"Expected {hint}, value was {type(value)}")
        return _map_value_to_type(
            hint=hint,
            map_value=value,
            origin=origin,
            type_args=type_args,
            custom_converters=custom_converters,
        )

    # Dataclass
    if dataclasses.is_dataclass(hint):
        if not isinstance(value, dict):
            raise TypeError(
                f"Cannot convert to dataclass {hint}, value is {type(value)} not dict"
            )
        # Obtain dataclass fields and check that all dict fields are there and
        # that no required fields are missing. Unknown fields are silently
        # ignored.
        fields = dataclasses.fields(hint)
        field_hints = get_type_hints(hint)
        field_values = {}
        for field in fields:
            field_value = value.get(field.name, dataclasses.MISSING)
            # We do not check whether field is required here. Rather, we let the
            # attempted instantiation of the dataclass raise if a field is
            # missing
            if field_value is not dataclasses.MISSING:
                try:
                    field_values[field.name] = value_to_type(
                        field_hints[field.name], field_value, custom_converters
                    )
                except Exception as err:
                    raise TypeError(
                        f"Failed converting field {field.name} on dataclass {hint}"
                    ) from err
        # Simply instantiate the dataclass. This will fail as expected when
        # missing required fields.
        # TODO(cretz): Want way to convert snake case to camel case?
        return hint(**field_values)

    # If there is a @staticmethod or @classmethod parse_obj, we will use it.
    # This covers Pydantic models.
    parse_obj_attr = inspect.getattr_static(hint, "parse_obj", None)
    if isinstance(parse_obj_attr, (classmethod, staticmethod)):
        if not isinstance(value, dict):
            raise TypeError(
                f"Cannot convert to {hint}, value is {type(value)} not dict"
            )
        return getattr(hint, "parse_obj")(value)

    # IntEnum
    if inspect.isclass(hint) and issubclass(hint, IntEnum):
        if not isinstance(value, int):
            raise TypeError(
                f"Cannot convert to enum {hint}, value not an integer, value is {type(value)}"
            )
        return hint(value)

    # StrEnum, available in 3.11+
    if sys.version_info >= (3, 11):
        if inspect.isclass(hint) and issubclass(hint, StrEnum):
            if not isinstance(value, str):
                raise TypeError(
                    f"Cannot convert to enum {hint}, value not a string, value is {type(value)}"
                )
            return hint(value)

    # UUID
    if inspect.isclass(hint) and issubclass(hint, uuid.UUID):
        return hint(value)

    # Iterable. We intentionally put this last as it catches several others.
    if inspect.isclass(origin) and issubclass(origin, collections.abc.Iterable):
        if not isinstance(value, collections.abc.Iterable):
            raise TypeError(f"Expected {hint}, value was {type(value)}")
        ret_list = []
        # If there is no type arg, just return value as is
        if not type_args or (
            len(type_args) == 1
            and (isinstance(type_args[0], TypeVar) or type_args[0] is Ellipsis)
        ):
            ret_list = list(value)
        else:
            # Otherwise convert
            for i, item in enumerate(value):
                # Non-tuples use first type arg, tuples use arg set or one
                # before ellipsis if that's set
                if origin is not tuple:
                    arg_type = type_args[0]
                elif len(type_args) > i and type_args[i] is not Ellipsis:
                    arg_type = type_args[i]
                elif type_args[-1] is Ellipsis:
                    # Ellipsis means use the second to last one
                    arg_type = type_args[-2]
                else:
                    raise TypeError(
                        f"Type {hint} only expecting {len(type_args)} values, got at least {i + 1}"
                    )
                try:
                    ret_list.append(value_to_type(arg_type, item, custom_converters))
                except Exception as err:
                    raise TypeError(f"Failed converting {hint} index {i}") from err
        # If tuple, set, or deque convert back to that type
        if origin is tuple:
            return tuple(ret_list)
        elif origin is set:
            return set(ret_list)
        elif origin is collections.deque:
            return collections.deque(ret_list)
        return ret_list

    raise TypeError(f"Unserializable type during conversion: {hint}")


def _map_value_to_type(
    hint: Type[Any],
    map_value: Any,
    origin: Type[Any],
    type_args: Tuple[Any, ...],
    custom_converters: Optional[Sequence[JSONTypeConverter]] = None,
) -> Any:
    ret_dict = {}
    # If there are required or optional keys that means we are a TypedDict
    # and therefore can extract per-key types
    per_key_types: Optional[Dict[str, Type[Any]]] = None
    if getattr(origin, "__required_keys__", None) or getattr(
        origin, "__optional_keys__", None
    ):
        per_key_types = get_type_hints(origin)
    key_type = (
        type_args[0]
        if len(type_args) > 0
        and type_args[0] is not Any
        and not isinstance(type_args[0], TypeVar)
        else None
    )
    value_type = (
        type_args[1]
        if len(type_args) > 1
        and type_args[1] is not Any
        and not isinstance(type_args[1], TypeVar)
        else None
    )
    # Convert each key/value
    for key, value in map_value.items():
        if key_type:
            try:
                key = value_to_type(key_type, key, custom_converters)
            except Exception as err:
                raise TypeError(f"Failed converting key {key} on {hint}") from err
        # If there are per-key types, use it instead of single type
        this_value_type = value_type
        if per_key_types:
            # TODO(cretz): Strict mode would fail an unknown key
            this_value_type = per_key_types.get(key)
        if this_value_type:
            try:
                value = value_to_type(this_value_type, value, custom_converters)
            except Exception as err:
                raise TypeError(
                    f"Failed converting value for key {key} on {hint}"
                ) from err
        ret_dict[key] = value
    # If there are per-key types, it's a typed dict and we want to attempt
    # instantiation to get its validation
    if per_key_types:
        ret_dict = hint(**ret_dict)
    return ret_dict
