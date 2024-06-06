"""A document is a set of text and metadata."""

from uuid import uuid4
from typing import Dict, Any, Optional, List

from pydantic import BaseModel, PrivateAttr, Field, computed_field

from .version import Version


class Document(BaseModel):
    """A document is a collection of text and metadata."""

    _id: str = PrivateAttr(default_factory=lambda: str(uuid4()))
    metadata: Dict[str, Any]

    name: Optional[str] = Field(
        default=None,
        description=(
            "An optional name for the document. Must be unique within the"
            " workflow the document exists in. Think of it like a filename."
        ),
    )

    path: str = Field(
        default="/", description="The path to the document in the workflow"
    )

    versions: List[Version] = Field(
        default=[], description="The versions of the document"
    )

    @computed_field  # type: ignore[misc]
    @property
    def id(self) -> str:
        """The workflow's unique identifier"""
        return self._id

    @computed_field  # type: ignore[misc]
    @property
    def task(self) -> str:
        """The task the document exists in"""
        parts = self.path.split("/")
        if len(parts) == 1:
            return "__start__"
        return parts[1]

    @computed_field  # type: ignore[misc]
    @property
    def step(self) -> str:
        """The step the document exists in"""
        parts = self.path.split("/")
        if len(parts) < 3:
            return "__start__"
        return parts[2]
