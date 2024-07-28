"""The context for a workflow"""

import logging
from typing import List, Optional

from fixpoint.agents import BaseAgent
from fixpoint.cache import SupportsChatCompletionCache
from .workflow import WorkflowRun
from ._wrapped_workflow_agents import WrappedWorkflowAgents


class WorkflowContext:
    """Context for a workflow.

    Holds all relevant context for a workflow. Pass this into every step
    function of your workflow.
    """

    agents: WrappedWorkflowAgents
    workflow_run: WorkflowRun
    cache: Optional[SupportsChatCompletionCache]
    logger: logging.Logger

    def __init__(
        self,
        workflow_run: WorkflowRun,
        agents: List[BaseAgent],
        cache: Optional[SupportsChatCompletionCache] = None,
        logger: Optional[logging.Logger] = None,
        *,
        _workflow_agents_override_: Optional[WrappedWorkflowAgents] = None,
    ) -> None:
        if _workflow_agents_override_ is None:
            self.agents = WrappedWorkflowAgents(agents, workflow_run)
        else:
            self.agents = _workflow_agents_override_
        self.workflow_run = workflow_run

        if cache:
            self.cache = cache
        elif workflow_run.storage_config and workflow_run.storage_config.agent_cache:
            self.cache = workflow_run.storage_config.agent_cache
        else:
            self.cache = None

        self.logger = logger or self._setup_logger(workflow_run)

    def _setup_logger(self, workflow_run: WorkflowRun) -> logging.Logger:
        logger = logging.getLogger(f"fixpoint/workflows/runs/{workflow_run.id}")
        # We need to add this stream handler, because otherwise I think the
        # logger is using the handler from the default logger, which has a
        # log-level of "warning". This means that we do not print "info" logs.
        c_handler = logging.StreamHandler()
        logger.addHandler(c_handler)
        logger.setLevel(logging.INFO)
        return logger

    def _update_workflow_run(self, workflow_run: WorkflowRun) -> None:
        self.workflow_run = workflow_run
        # pylint: disable=protected-access
        self.agents._update_agents(workflow_run)

    def clone(
        self, new_task: str | None = None, new_step: str | None = None
    ) -> "WorkflowContext":
        """Clones the workflow context"""
        # clone the workflow run
        new_workflow_run = self.workflow_run.clone(new_task=new_task, new_step=new_step)
        # clone the agents
        new_agents = self.agents.clone(new_workflow_run)

        return self.__class__(
            agents=[],
            workflow_run=new_workflow_run,
            cache=self.cache,
            logger=self.logger,
            _workflow_agents_override_=new_agents,
        )
