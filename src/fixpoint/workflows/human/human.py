"""Human in the loop functionality"""

import os
from typing import Any, List, Optional
from pydantic import BaseModel, Field, PrivateAttr, SkipValidation
from supabase import create_client, Client
from fixpoint._utils.ids import make_resource_uuid

from fixpoint.workflows.node_state import WorkflowStatus


class EditableConfig(BaseModel):
    """
    The editable config for a field.
    """

    is_editable: bool = Field(description="Whether the field is editable", default=True)
    is_required: bool = Field(
        description="Whether the field is required", default=False
    )
    human_contents: Any = Field(description="The human contents", default=None)


class EntryField(BaseModel):
    """
    A field that can be edited by a human.
    """

    id: str = Field(description="The field id")
    display_name: Optional[str] = Field(description="The display name", default=None)
    description: Optional[str] = Field(description="The description", default=None)
    contents: Optional[Any] = Field(description="The contents", default=None)
    editable_config: EditableConfig = Field(
        description="The editable config",
        default_factory=EditableConfig,
    )


def new_task_entry_id() -> str:
    """Create a new workflow run id"""
    return make_resource_uuid("ht")


class HumanTaskEntry(BaseModel):
    """
    A task entry that a human can complete.
    """

    id: str = Field(
        description="The id of task entry", default_factory=new_task_entry_id
    )
    task_id: str = Field(description="The task id")
    workflow_id: str = Field(description="The workflow id")
    workflow_run_id: str = Field(description="The workflow run id")
    source_node: Optional[str] = Field(
        description="Node that created the task", default=None
    )

    status: str = Field(
        description="The status of the task", default=WorkflowStatus.SUSPENDED.value
    )
    entry_fields: List[EntryField] = Field(description="Entry fields", default=[])
    original_model: SkipValidation[BaseModel] = Field(
        description="The original model", exclude=True
    )

    def model_post_init(self, __context: Any) -> None:
        if not self.entry_fields:
            self.entry_fields = self._original_model_to_entry_fields(
                self.original_model
            )

    def to_original_model(self) -> BaseModel:
        """Converts a human task into an instance of the type of the original model"""
        new_data = {
            item.id: item.editable_config.human_contents or item.contents
            for item in self.entry_fields
        }
        return self.original_model.__class__(**new_data)

    def _original_model_to_entry_fields(
        self, original_model: BaseModel
    ) -> List[EntryField]:
        """Converts an original model into a list of entry fields"""
        entry_fields = []
        for field_name, field_info in original_model.model_fields.items():
            field_value = getattr(original_model, field_name)
            ef = EntryField(
                id=field_name,
                # TODO(jakub): Perhaps making display_name prettier is the solution?
                display_name=None,
                description=field_info.description,
                contents=field_value,
            )
            entry_fields.append(ef)

        return entry_fields


class HumanInTheLoop(BaseModel):
    """Human in the loop"""

    workflow_id: str = Field(description="The workflow id")
    workflow_run_id: str = Field(description="The workflow run id")

    tasks: List[HumanTaskEntry] = Field(description="The tasks", default=[])
    _db_client: Optional[Client] = PrivateAttr(default=None)

    def model_post_init(self, __context: Any) -> None:
        # TODO(jakub): Validate these appropriately
        # Ensure that these are defined
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_ANON_KEY")
        if supabase_url and supabase_key:
            self._db_client = create_client(supabase_url, supabase_key)
        else:
            print("Warning: HumanInTheLoop > Database client not initialized")

    def send_task_entry(
        self, task_id: str, original_model: BaseModel
    ) -> HumanTaskEntry:
        """Sends a task entry"""
        task = HumanTaskEntry(
            task_id=task_id,
            workflow_id=self.workflow_id,
            workflow_run_id=self.workflow_run_id,
            original_model=original_model,
        )
        model_dump = task.model_dump()
        if self._db_client is None:
            raise AttributeError("Database client is not initialized")

        self._db_client.table("task_entries").insert(model_dump).execute()

        return task

    def get_task_entry(
        self, task_entry_id: str, original_model: BaseModel
    ) -> HumanTaskEntry | None:
        """Retrieves a task"""
        if self._db_client is None:
            raise AttributeError("Database client is not initialized")

        response = (
            self._db_client.table("task_entries")
            .select("*")
            .eq("id", task_entry_id)
            .execute()
        )

        if len(response.data) == 0:
            return None
        task = HumanTaskEntry(**response.data[0], original_model=original_model)

        return task
