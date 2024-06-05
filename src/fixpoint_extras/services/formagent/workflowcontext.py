"""The context for a workflow"""

from collections import defaultdict
import dataclasses
from dataclasses import dataclass
import logging
from typing import Dict, List, Optional, Type, Tuple

from pydantic import BaseModel, Field, FieldInfo

import fixpoint
from fixpoint.cache import SupportsChatCompletionCache
from fixpoint.analyze.memory import DataframeMemory


class TaskForm(BaseModel):
    task_id: str
    step_id: str
    definition: Type[BaseModel] = Field(description="The spec for the form fields")
    form: BaseModel = Field(description="The (partially) filled form")

    def missing_fields(self) -> Dict[str, FieldInfo]:
        """Get the fields that do not yet have answers."""
        missing: Dict[str, FieldInfo] = {}
        for k, v in self.info.model_dump().items():
            if v is None:
                missing[k] = self.info_model.model_fields[k]
        return missing

    def is_complete(self) -> bool:
        """True if all form info has been filled in."""
        missing = self.missing_fields()
        return len(missing) == 0


@dataclass
class WorkflowContext:
    """Context for a workflow.

    Holds all relevant context for a workflow. Pass this into every step
    function of your workflow.
    """

    agent: fixpoint.agents.BaseAgent
    logger: logging.Logger
    memory: DataframeMemory
    workflow: fixpoint.workflow.Workflow
    cache: Optional[SupportsChatCompletionCache]
    current_task_id: str
    current_step_id: str

    # this is a dict mapping from task ID to step ID to task form
    _task_forms: Dict[str, Dict[str, Dict[str, TaskForm]]] = dataclasses.field(
        default_factory=defaultdict(lambda: defaultdict(dict)),
        init=False,
        repr=False,
    )

    def get_task_form(self, task_id: str, form_id: str) -> TaskForm:
        """Get a task form by its ID."""
        return self._task_forms[task_id][form_id]

    def list_task_forms(self, task_id: str) -> List[Tuple[str, TaskForm]]:
        """List all task forms for a task."""
        return list(self._task_forms[task_id].items())

    def set_task_form(self, task_id: str, form_id: str, form: TaskForm) -> None:
        """Set a task form."""
        self._task_forms[task_id][form_id] = form
