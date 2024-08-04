"""A document is a set of text and metadata."""

from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field, computed_field

from fixpoint.workflows.constants import TASK_MAIN_ID, STEP_MAIN_ID
from ._version import Version


class Document(BaseModel):
    """A document is a collection of text and metadata."""

    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Metadata for document"
    )

    id: str = Field(
        description=("Must be unique within the workflow the document exists in."),
    )

    path: str = Field(
        default="/", description="The path to the document in the workflow"
    )

    versions: List[Version] = Field(
        default=[], description="The versions of the document"
    )

    contents: str = Field(description="The contents of the document")

    workflow_id: Optional[str] = Field(description="The workflow id")
    workflow_run_id: Optional[str] = Field(description="The workflow run id")

    @computed_field  # type: ignore[misc]
    @property
    def task(self) -> str:
        """The task the document exists in"""
        parts = self.path.split("/")
        if len(parts) == 1:
            return TASK_MAIN_ID
        return parts[0]

    @computed_field  # type: ignore[misc]
    @property
    def step(self) -> str:
        """The step the document exists in"""
        parts = self.path.split("/")
        if len(parts) < 3:
            return STEP_MAIN_ID
        return parts[2]
