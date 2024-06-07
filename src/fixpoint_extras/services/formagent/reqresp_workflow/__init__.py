from typing import List, Literal, Optional, Type, Union

from pydantic import BaseModel, Field

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


class FormAgentWorkflowDefinition(BaseModel):
    tasks: List[FormAgentTask]


# def new_classify_model() -> Type[BaseModel]:
#     class Classify(BaseModel):
#         """Classify the eval and do chain of thought"""

#         chain_of_thought: str = Field(description=)


# def create_workflow(
#     *, workflow_name: Optional[str] = None, definition: FormAgentWorkflowDefinition
# ) -> Workflow:
#     w = Workflow(name=workflow_name)
#     w.forms.store()
