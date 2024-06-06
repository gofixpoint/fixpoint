"""The context for a workflow"""

from dataclasses import dataclass
import logging
from typing import Optional

import fixpoint
from fixpoint.workflow import SupportsWorkflow
from fixpoint.cache import SupportsChatCompletionCache
from fixpoint.analyze.memory import DataframeMemory


@dataclass
class WorkflowContext:
    """Context for a workflow.

    Holds all relevant context for a workflow. Pass this into every step
    function of your workflow.
    """

    agent: fixpoint.agents.BaseAgent
    logger: logging.Logger
    memory: DataframeMemory
    workflow: SupportsWorkflow
    cache: Optional[SupportsChatCompletionCache]

    @classmethod
    def from_workflow(cls, workflow: SupportsWorkflow, agent: fixpoint.agents.BaseAgent, memory: DataframeMemory, cache: Optional[SupportsChatCompletionCache] = None) -> "WorkflowContext":
        return cls(agent=agent, logger=logging.getLogger(f"fixpoint_workflow/runs/{workflow.run_id}"), memory=memory, workflow=workflow, cache=cache)
