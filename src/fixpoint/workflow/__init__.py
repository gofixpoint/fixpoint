"""Agents work in a "workflow".

A "workflow" is a series of steps that one or more agents takes to accomplish
some goal.
"""

from ._workflow import WorkflowRun
from .protocol import SupportsWorkflowRun

__all__ = ["WorkflowRun", "SupportsWorkflowRun"]
