"""A base protocol for models"""

from typing import Protocol


class BaseModel(Protocol):
    """A base protocol for models"""

    model_name: str
