from uuid import uuid4
from typing import Dict, Any, Optional

from pydantic import BaseModel, PrivateAttr, Field


class Version(BaseModel):
    num: int = Field(description="The version number of the document. Increases monotonically")
    path: str = Field(description="For this version, the path to the task and step where we updated the document")


class Document(BaseModel):
    """A document is a collection of text and metadata."""

    _id: str = PrivateAttr(default_factory=lambda: str(uuid4()))
    metadata: Dict[str, Any]

    name: Optional[str] = Field(
        default=None,
        description=(
            "An optional name for the workflow. Must be unique within the workspace."
            " Think of it like a filename."
        ),
    )

    path: str = Field(default="/", description="The path to the document in the workflow")

    @computed_field  # type: ignore[misc]
    @property
    def id(self) -> str:
        """The workflow's unique identifier"""
        return self._id

    @computed_field  # type: ignore[misc]
    @property
    def task(self) -> str:
        """The workflow's unique identifier"""
        parts = self.path.split("/")
        if len(parts) == 1:
            return "__start__"
        return parts[1]


    @computed_field  # type: ignore[misc]
    @property
    def step(self) -> str:
        """The workflow's unique identifier"""
        parts = self.path.split("/")
        if len(parts) < 3:
            return "__start__"
        return parts[2]
