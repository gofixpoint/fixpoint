"""The context for a workflow"""

from dataclasses import dataclass
import logging
from typing import Dict

import fixpoint


@dataclass
class WorkflowContext:
    """Context for a workflow.

    Holds all relevant context for a workflow. Pass this into every step
    function of your workflow.
    """

    agents: Dict[str, fixpoint.agents.BaseAgent]
    logger: logging.Logger
    workflow: fixpoint.workflow.Workflow
