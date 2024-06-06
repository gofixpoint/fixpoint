"""A form is a set of fields for a user or agent to fill in."""

from uuid import uuid4
from typing import Dict, Any, Optional, List, Type, TypeVar, Generic

from pydantic import BaseModel, PrivateAttr, Field, computed_field

from .version import Version

T = TypeVar("T", bound=BaseModel)


class Form(BaseModel, Generic[T]):
    """A form is a collection of fields for a user or agent to fill in."""

    _id: str = PrivateAttr(default_factory=lambda: str(uuid4()))
    metadata: Dict[str, Any]

    name: Optional[str] = Field(
        default=None,
        description=(
            "An optional name for the form. Must be unique within the"
            " workflow the form exists in. Think of it like a filename."
        ),
    )

    path: str = Field(default="/", description="The path to the form in the workflow")

    versions: List[Version] = Field(
        default=[], description="The versions of the document"
    )

    @computed_field  # type: ignore[misc]
    @property
    def id(self) -> str:
        """The form's unique identifier"""
        return self._id

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

    # This is the actual form schema and contents

    # We can't name it "schema" because that conflicts with a Pydantic method
    form_schema: Type[T] = Field(description="The form schema", alias="schema")

    _contents: T = PrivateAttr()

    @computed_field  # type: ignore[misc]
    @property
    def contents(self) -> T:
        """The (partially or fully) filled in form contents"""
        return self._contents

    def set_contents(self, contents: T) -> None:
        """Set the filled in form contents"""
        self._contents = contents

    def model_post_init(self, _context: Any) -> None:
        """Run Pydantic model post init code"""
        self._contents = self.form_schema()
