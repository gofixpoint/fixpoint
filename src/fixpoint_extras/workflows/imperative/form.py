"""A form is a set of fields for a user or agent to fill in."""

import importlib
from typing import Dict, Any, List, Type, TypeVar, Generic, Union, cast

from pydantic import BaseModel, PrivateAttr, Field, computed_field, field_validator

from .version import Version

T = TypeVar("T", bound=BaseModel)


class Form(BaseModel, Generic[T]):
    """A form is a collection of fields for a user or agent to fill in."""

    id: str = Field(
        description="Must be unique within the workflow the form exists in."
    )
    metadata: Dict[str, Any] = Field(default={}, description="Metadata for the form")

    path: str = Field(default="/", description="The path to the form in the workflow")

    versions: List[Version] = Field(
        default=[], description="The versions of the document"
    )

    workflow_run_id: str = Field(description="The workflow run id")

    # Manually override model_dump_json
    def model_dump(self, *_: Any, **__: Any) -> dict[str, Any]:
        data = super().model_dump()
        data["form_schema"] = (
            f"{self.form_schema.__module__}.{self.form_schema.__name__}"
        )
        return data

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
    @field_validator("form_schema", mode="before")
    @classmethod
    def convert_string_to_class(cls, v: str) -> Type[T]:
        """Convert a string to a class"""
        if isinstance(v, str):
            module_name, class_name = v.rsplit(".", 1)
            module = importlib.import_module(module_name)
            v = getattr(module, class_name)
            return cast(Type[T], v)
        return v

    # We can't name it "schema" because that conflicts with a Pydantic method
    form_schema: Type[T] = Field(description="The form schema")

    _contents: T = PrivateAttr()

    @computed_field  # type: ignore[misc]
    @property
    def contents(self) -> T:
        """The (partially or fully) filled in form contents"""
        return self._contents

    def set_contents(self, contents: Union[T, Dict[str, Any]]) -> None:
        """Set the filled in form contents"""
        if isinstance(contents, dict):
            self._contents = self.form_schema(**contents)
        else:
            self._contents = contents

    @field_validator("form_schema")
    @classmethod
    def _validate_form_schema(cls, form_schema: Type[T]) -> Type[T]:
        # TODO(dbmikus) test this

        # check that every field in the form_schema is optional. These are Pydantic fields
        for name, field in form_schema.model_fields.items():
            if field.get_default() is not None:
                raise ValueError(
                    f'Form field "{name}" must have a default value of None, '
                    "so the agent can fill it in later"
                )

        # make sure that each form field is not a nested type like a list,
        # dictionary, object, or other complex types
        for name, field in form_schema.model_fields.items():
            if isinstance(field.annotation, (list, dict, BaseModel, tuple, set)):
                raise ValueError(
                    f'Form field "{name}" must be a primitive type, '
                    "not a complex type like list, dict, object, tuple, or set, "
                    "so the agent can fill it in later"
                )

        return form_schema

    def model_post_init(self, _context: Any) -> None:
        """Run Pydantic model post init code"""
        self._contents = self.form_schema()
