from uuid import uuid4
from typing import Dict, Any, Optional

from pydantic import BaseModel, PrivateAttr, Field

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

    @computed_field  # type: ignore[misc]
    @property
    def id(self) -> str:
        """The workflow's unique identifier"""
        return self._id
