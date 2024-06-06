from typing import List, Literal, Optional, Union

from pydantic import BaseModel

from fixpoint.workflow import SupportsWorkflow
from fixpoint_extras.workflows.imperative import Workflow


class FormAgentTask(BaseModel):
    task_name: str
    fields: List["BaseModel"]
    next: Union["NextChoice", "NextAlways", "NextDone"]


class NextChoice(BaseModel):
    choices: List["ChoiceEntry"]
    next_task_name: str


class NextAlways(BaseModel):
    next_task_name: str


class NextDone(BaseModel):
    terminal: Literal[True] = True


class ChoiceEntry(BaseModel):
    label: str
    description: str


class OmellaWorkflowDefinition(BaseModel):
    tasks: List[FormAgentTask]


def create_workflow(
    *,
    workflow_name: Optional[str] = None,
    definition: OmellaWorkflowDefinition
) -> Workflow:
    w = Workflow(name=workflow_name)
    w.forms.store
