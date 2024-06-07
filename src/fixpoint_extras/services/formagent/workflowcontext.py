"""The context for a workflow"""

from dataclasses import dataclass
import logging
from typing import Optional

import fixpoint
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
    workflow_run: fixpoint.workflow.SupportsWorkflowRun
    cache: Optional[SupportsChatCompletionCache]
