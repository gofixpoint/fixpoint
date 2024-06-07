"""A form is a set of fields for a user or agent to fill in."""

from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field, computed_field

from .version import Version


class Form(BaseModel):
    """A form is a collection of fields for a user or agent to fill in."""

    metadata: Dict[str, Any]

    id: Optional[str] = Field(
        default=None,
        description=("Must be unique within the workflow the form exists in."),
    )

    path: str = Field(default="/", description="The path to the form in the workflow")

    versions: List[Version] = Field(
        default=[], description="The versions of the document"
    )

    @computed_field  # type: ignore[misc]
    @property
    def task(self) -> str:
        """The task the form exists in"""
        parts = self.path.split("/")
        if len(parts) == 1:
            return "__start__"
        return parts[1]

    @computed_field  # type: ignore[misc]
    @property
    def step(self) -> str:
        """The step the form exists in"""
        parts = self.path.split("/")
        if len(parts) < 3:
            return "__start__"
        return parts[2]
