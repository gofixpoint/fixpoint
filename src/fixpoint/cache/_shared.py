"""shared internal code for the caching module"""

import json
from typing import Any

from ..logging import logger as root_logger


logger = root_logger.getChild("cache")


def serialize_any(key: Any) -> str:
    """Serialize anything to a string"""
    if isinstance(key, (dict, list, set, str, int, float, bool)):
        return json.dumps(key)
    return str(key)
