"""The context for a workflow"""

import logging
from typing import Dict, Optional

from fixpoint.agents import BaseAgent
from fixpoint.cache import SupportsChatCompletionCache
from fixpoint.memory import NoOpMemory, Memory
from .workflow import WorkflowRun


class WorkflowContext:
    """Context for a workflow.

    Holds all relevant context for a workflow. Pass this into every step
    function of your workflow.
    """

    agents: Dict[str, BaseAgent]
    workflow_run: WorkflowRun
    cache: Optional[SupportsChatCompletionCache]
    logger: logging.Logger

    def __init__(
        self,
        agents: Dict[str, BaseAgent],
        workflow_run: WorkflowRun,
        cache: Optional[SupportsChatCompletionCache] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.agents = self._prepare_agents(agents)
        self.workflow_run = workflow_run
        self.cache = cache
        self.logger = logger or logging.getLogger(
            f"fixpoint/workflows/runs/{workflow_run.id}"
        )

    def _prepare_agents(self, agents: Dict[str, BaseAgent]) -> Dict[str, BaseAgent]:
        for agent in agents.values():
            # We require agents in a workflow to have working memory
            if isinstance(agent.memory, NoOpMemory):
                agent.memory = Memory()
        return agents

    @classmethod
    def from_workflow(
        cls,
        workflow_run: WorkflowRun,
        agents: Dict[str, BaseAgent],
        cache: Optional[SupportsChatCompletionCache] = None,
    ) -> "WorkflowContext":
        """Creates a WorkflowContext for a workflow"""
        return cls(
            agents=agents,
            workflow_run=workflow_run,
            cache=cache,
            logger=logging.getLogger(f"fixpoint/workflows/runs/{workflow_run.id}"),
        )
