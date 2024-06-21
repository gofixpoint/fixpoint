"""The context for a workflow"""

from dataclasses import dataclass
import logging
from typing import Dict, Optional

import fixpoint
from fixpoint.cache import SupportsChatCompletionCache
from fixpoint.analyze.memory import DataframeMemory
from .workflow import WorkflowRun


@dataclass
class WorkflowContext:
    """Context for a workflow.

    Holds all relevant context for a workflow. Pass this into every step
    function of your workflow.
    """

    agents: Dict[str, fixpoint.agents.BaseAgent]
    logger: logging.Logger
    memory: DataframeMemory
    workflow_run: WorkflowRun
    cache: Optional[SupportsChatCompletionCache]

    @classmethod
    def from_workflow(
        cls,
        workflow_run: WorkflowRun,
        agents: Dict[str, fixpoint.agents.BaseAgent],
        memory: DataframeMemory,
        cache: Optional[SupportsChatCompletionCache] = None,
    ) -> "WorkflowContext":
        """Creates a WorkflowContext for a workflow"""
        return cls(
            agents=agents,
            logger=logging.getLogger(f"fixpoint/workflows/runs/{workflow_run.id}"),
            memory=memory,
            workflow_run=workflow_run,
            cache=cache,
        )
