"""A version of a document or form."""

from pydantic import BaseModel, Field


class Version(BaseModel):
    """A version of a document or form."""

    num: int = Field(
        description="The version number of the object. Increases monotonically"
    )
    path: str = Field(
        description="For this version, the path is the task and step where we updated the object"
    )
