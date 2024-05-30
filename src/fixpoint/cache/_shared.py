"""shared internal code for the caching module"""

import json
from typing import Any


def hash_key(key: Any) -> int:
    """Hash a key to an int"""
    if isinstance(key, (dict, list, set)):
        # Convert unhashable types to a JSON string
        try:
            key_str = json.dumps(key, sort_keys=True)
        except TypeError as e:
            # Handle types that are not serializable by json.dumps
            raise ValueError(f"Key of type {type(key)} is not serializable: {e}") from e

        return hash(key_str)
    return hash(key)
