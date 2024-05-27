"""Agents work in a "workflow".

A "workflow" is a series of steps that one or more agents takes to accomplish
some goal.
"""

from ._workflow import Workflow
from .protocol import SupportsWorkflow

__all__ = ["Workflow", "SupportsWorkflow"]
