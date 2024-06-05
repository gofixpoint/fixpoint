"""Simple implementation of a workflow"""

from dataclasses import dataclass
from uuid import uuid4
from typing import Optional

from pydantic import BaseModel, Field, PrivateAttr, computed_field


class Workflow(BaseModel):
    """A simple workflow implementation"""

    _id: str = PrivateAttr(default_factory=lambda: str(uuid4()))

    name: Optional[str] = Field(
        default=None,
        description=(
        "An optional name for the workflow. Must be unique within the workspace."
        " Think of it like a filename."
        )
    )

    # @property
    @computed_field
    def id(self) -> str:
        """The workflow's unique identifier"""
        return self._id
