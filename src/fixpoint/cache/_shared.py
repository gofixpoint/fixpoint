"""shared internal code for the caching module"""

import json
from typing import Any

from ..logging import logger as root_logger


logger = root_logger.getChild("cache")


def hash_key(key: Any) -> int:
    """Hash a key to an int"""
    logger.debug("Hashing key of type: %s", type(key))
    if isinstance(key, (dict, list, set, str)):
        # Convert unhashable types to a JSON string
        try:
            key_str = json.dumps(key, sort_keys=True)
            logger.debug("Hashed key is: %s", key_str)
        except TypeError as e:
            # Handle types that are not serializable by json.dumps
            raise ValueError(f"Key of type {type(key)} is not serializable: {e}") from e

        return hash(key_str)
    return hash(key)
