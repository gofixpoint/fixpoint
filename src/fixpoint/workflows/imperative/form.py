"""A form is a set of fields for a user or agent to fill in."""

import json
from typing import (
    Dict,
    Any,
    List,
    Type,
    TypeVar,
    Generic,
    Union,
    Optional,
    get_origin,
    get_args,
)

from pydantic import (
    BaseModel,
    PrivateAttr,
    Field,
    computed_field,
    create_model,
    field_validator,
)

from ._version import Version


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

    workflow_id: str = Field(description="The workflow id")
    workflow_run_id: str = Field(description="The workflow run id")

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

    # We can't name it "schema" because that conflicts with a Pydantic method
    form_schema: Type[T] = Field(description="The form schema")

    _contents: T = PrivateAttr()

    @computed_field  # type: ignore[misc]
    @property
    def contents(self) -> T:
        """The (partially or fully) filled in form contents"""
        return self._contents

    def update_contents(self, contents: Union[T, Dict[str, Any]]) -> None:
        """Update the filled in form contents

        We preserve old fields, only setting in the values that are passed in.
        """
        if isinstance(contents, dict):
            allowed_fields = set(self.form_schema.model_fields.keys())
            for key in contents.keys():
                if key not in allowed_fields:
                    raise ValueError(f'Form field "{key}" is not allowed')

        if not isinstance(contents, BaseModel):
            # Validate the contents according to the schema. Only necessary if
            # we got a dict.
            contents = self.form_schema(**contents)

        contents_dict = contents.model_dump(include=contents.model_fields_set)
        new_contents = self.contents.model_copy(update=contents_dict)
        self._contents = new_contents

    @field_validator("form_schema")
    @classmethod
    def _validate_form_schema(cls, form_schema: Type[T]) -> Type[T]:
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
            if not _is_valid_field_annotation(field.annotation):
                raise ValueError(
                    f'Form field "{name}" must be a primitive type, '
                    "not a complex type like list, dict, object, tuple, or set, "
                    "so the agent can fill it in later"
                )

        return form_schema

    @classmethod
    def _create_pydantic_model_from_json_schema(
        cls, schema: Dict[str, Any]
    ) -> Type[BaseModel]:
        """
        Dynamically creates a Pydantic model from a JSON schema.

        Args:
        - schema (Dict[str, Any]): The JSON schema dictionary.
        - model_name (str): The name of the model to create.

        Returns:
        - Type[BaseModel]: A dynamically created Pydantic model.
        """
        fields: Dict[str, Any] = {}

        model_name = schema.get("title", "UnnamedModel")
        if not isinstance(model_name, str):
            raise ValueError("Form JSON schema has no title")
        properties = schema.get("properties", {})
        if not properties:
            raise ValueError("Form JSON schema has no properties")

        for field_name, details in properties.items():
            if "anyOf" not in details:
                raise ValueError("Form JSON schema is invalid")
            type_strings = [option["type"] for option in details["anyOf"]]
            if "null" not in type_strings:
                raise ValueError(
                    f"Form JSON schema: field {field_name} must be optional"
                )
            field_types: List[Type[Any]] = [
                cls._json_schema_type_to_py_type(t)
                for t in type_strings
                # remove null types because we process them below
                if t != "null"
            ]

            if len(field_types) == 0:
                raise ValueError(
                    f"Form JSON schema: field {field_name} must have at least one type"
                )
            pytype: Any
            if len(field_types) == 1:
                pytype = Optional[field_types[0]]
            else:
                pytype = Optional[Union[*field_types]]

            field_description = details.get("description", None)
            field_default = details.get("default", None)
            field = Field(default=field_default, description=field_description)

            # Add more complex type handling here as needed
            fields[field_name] = (pytype, field)

        return create_model(model_name, **fields)

    @classmethod
    def _json_schema_type_to_py_type(cls, t: str) -> Type[Any]:
        if t == "string":
            return str
        elif t == "integer":
            return int
        elif t == "number":
            return float
        elif t == "boolean":
            return bool
        raise ValueError(f'Form field type "{t}" is not supported')

    def serialize(self) -> Dict[str, Any]:
        """Serialize the form to a string"""
        m = self.model_dump()
        del m["form_schema"]
        m["form_schema"] = self.form_schema.model_json_schema()
        m["contents"] = self.contents.model_dump()
        return m

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> "Form[BaseModel]":
        """Deserialize the form from a string"""
        data = data.copy()
        form_schema = data.pop("form_schema")
        if isinstance(form_schema, str):
            form_schema = json.loads(form_schema)
        contents = data.pop("contents")
        newdata = dict(data)
        newdata["form_schema"] = cls._create_pydantic_model_from_json_schema(
            form_schema
        )
        # If we do `form = cls(**newdata)`, Pydantic has errors like:
        # E    form_schema
        # E    Input should be a subclass of TicketOrderForm ...
        #
        # Because we dynamically deseriailize the JSON schema into a dynamically
        # create Pydantic model, we won't actually subclass the originally
        # defined form schema model.
        form = Form[BaseModel](**newdata)
        form.update_contents(contents)
        return form

    def model_post_init(self, _context: Any) -> None:
        """Run Pydantic model post init code"""
        self._contents = self.form_schema()


def _is_valid_field_annotation(annotation: Union[type, object, None]) -> bool:
    if annotation is None:
        return False

    typeorigin = get_origin(annotation)
    # typing.Optional becomes typing.Union[..., None]
    if typeorigin != Union:
        return False
    typeargs = get_args(annotation)
    if len(typeargs) < 2:
        return False
    found_nonetype = False
    for t in typeargs:
        if t is type(None):
            found_nonetype = True
        else:
            if t not in (int, str, float, bool):
                return False

    return found_nonetype
