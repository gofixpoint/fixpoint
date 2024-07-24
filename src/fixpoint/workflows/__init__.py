"""Agents work in a "workflow".

A "workflow" is a series of steps that one or more agents takes to accomplish
some goal.
"""

__all__ = ["Workflow", "WorkflowRun", "WorkflowStatus", "TASK_MAIN_ID", "STEP_MAIN_ID"]

from .constants import TASK_MAIN_ID, STEP_MAIN_ID
from ._workflow import Workflow, WorkflowRun
from .node_state import WorkflowStatus
