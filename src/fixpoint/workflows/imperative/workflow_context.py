"""The context for a workflow"""

import logging
from typing import List, Optional

from fixpoint.agents import BaseAgent
from fixpoint.cache import SupportsChatCompletionCache
from .workflow import Workflow, WorkflowRun
from .config import StorageConfig
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

        self.logger = logger or logging.getLogger(
            f"fixpoint/workflows/runs/{workflow_run.id}"
        )

    def _update_workflow_run(self, workflow_run: WorkflowRun) -> None:
        self.workflow_run = workflow_run
        # pylint: disable=protected-access
        self.agents._update_agents(workflow_run)

    @classmethod
    def load_from_workflow_run(
        cls,
        workflow: Workflow,
        workflow_run_id: str,
        agents: List[BaseAgent],
        storage_config: Optional[StorageConfig] = None,
    ) -> "WorkflowContext":
        """Load a workflow run's context from a workflow run id"""
        run = workflow.load_run(workflow_run_id=workflow_run_id)
        if not run:
            raise ValueError(f"Workflow run {workflow_run_id} not found")
        if storage_config:
            cache = storage_config.agent_cache
        else:
            cache = None
        return cls(workflow_run=run, agents=agents, cache=cache)

    @property
    def wfrun(self) -> WorkflowRun:
        """The workflow run"""
        return self.workflow_run

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
